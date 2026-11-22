from datetime import datetime, timezone
import logging
from typing import Any

from flask import Blueprint, request, jsonify, session

from modules.repositories.conversations import Conversation
from modules.services.conversations import ConversationSummary
from modules.services.container import get_services
from utils import error_response, login_required
from modules.real_time_socket.extensions import socketio

log = logging.getLogger(__name__)

conversations_bp = Blueprint('conversation_bp', __name__, url_prefix='/api/conversations')


def _format_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _serialize_summary(summary: ConversationSummary) -> dict[str, Any]:
    last_message = summary.last_message
    return {
        "conversation_id": summary.conversation_id,
        "conversation_type": summary.conversation_type,
        "receiver_id": summary.receiver_id,
        "display_name": summary.display_name,
        "conversation_img_url": summary.conversation_img_url,
        "latest_message": (
            {
                "message_id": str(last_message.message_id),
                "sender_id": last_message.sender_id,
                "sender_display_name": last_message.sender_name,
                "message_type": "text",
                "content": last_message.content,
                "created_at": _format_utc_iso(last_message.sent_at),
            }
            if last_message is not None
            else None
        ),
        "unread_count": summary.unread_count,
    }


def _serialize_created(
    conversation: Conversation,
    receiver_display_name: str,
    receiver_id: int | None,
) -> dict[str, Any]:
    return {
        "conversation_id": conversation.conversation_id,
        "conversation_type": conversation.type,
        "receiver_id": receiver_id,
        "receiver_display_name": receiver_display_name,
        "conversation_img_url": None,
    }


@conversations_bp.route('/', methods=['GET'])
@login_required
def get_conversations():
    user_id = session.get('user_id')
    conversations, err = get_services().conversations.list_for_user(user_id)
    if err or conversations is None:
        return error_response('Internal server error', 500)
    return jsonify([_serialize_summary(item) for item in conversations]), 200


@conversations_bp.route('/new-group', methods=['POST'])
@login_required
def create_group():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error_response("Body must be a JSON object", 400)

    group_name = body.get('group_name', '')
    member_ids = body.get('member_ids', [])

    if not isinstance(group_name, str):
        return error_response('Group name must not be empty', 400)
    group_name = group_name.strip()
    if not group_name:
        return error_response('Group name must not be empty', 400)
    if len(group_name) > 100:
        return error_response('Group name too long', 400)

    if not isinstance(member_ids, list) or not member_ids:
        return error_response('Must include at least one member', 400)
    if len(member_ids) > 99:
        return error_response('Too many members', 400)
    if any(
        isinstance(member_id, bool)
        or not isinstance(member_id, int)
        or member_id <= 0
        for member_id in member_ids
    ):
        return error_response('member_ids must contain positive integers', 400)
    if len(set(member_ids)) != len(member_ids):
        return error_response('member_ids must not contain duplicates', 400)

    user_id = session.get('user_id')

    if user_id in member_ids:
        return error_response('Must not contain self', 400)

    group, err = get_services().conversations.create_group(user_id, group_name, member_ids)
    if err:
        if err == 'Some users do not exist':
            return error_response('User not found', 404)
        if err.startswith(('Group name must be', 'Invalid group', 'At most ')):
            return error_response(err, 400)
        return error_response('Internal server error', 500)
    if group is None:
        return error_response('Internal server error', 500)
    return jsonify(_serialize_created(group, group.name or '', None)), 201


@conversations_bp.route('/new-conversation', methods=['POST'])
@login_required
def create_conversation():
    friend_id = request.args.get('user_id', 0, type=int)
    if not friend_id:
        return error_response('user_id invalid', 400)

    user_id = session.get('user_id')

    if friend_id == user_id:
        return error_response('Cannot start a conversation with yourself', 400)

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error_response("Body must be a JSON object", 400)

    message = body.get('message', '')
    if not isinstance(message, str) or not message.strip():
        return error_response('message must not be empty', 400)
    if len(message) > 2000:
        return error_response('message too long', 400)

    started, err = get_services().messages.start_direct_conversation(
        user_id, friend_id, message
    )
    if err:
        if err == 'Conversation already exists':
            return error_response(err, 409)
        if err == 'User not found':
            return error_response(err, 404)
        if err == 'Cannot start a conversation with yourself':
            return error_response(err, 400)
        if err.startswith(('Message', 'message', 'Cannot send message')):
            return error_response(err, 400)
        # Without this line the real cause is hidden behind a plain 500
        log.error("new-conversation failed: user=%s other=%s err=%s", user_id, friend_id, err)
        return error_response('Internal server error', 500)
    if started is None:
        return error_response('Internal server error', 500)
    summary = started.conversation
    msg = started.message
    created_at_iso = _format_utc_iso(msg.created_at)
    sender_display_name = (
        get_services().users.get_display_names([user_id]).get(user_id) or str(msg.sender_id)
    )

    socket_payload = {
        "sender_info": {
            "user_id": msg.sender_id,
            "username": getattr(msg, "sender_username", None) or "",
            "display_name": sender_display_name,
            "avatar_url": getattr(msg, "sender_avatar_url", None),
        },
        "conversation_id": summary.conversation_id,
        "message": msg.content,
        "message_type": "text",
        "message_id": str(msg.message_id),
        "created_at": created_at_iso,
    }

    socketio.emit(
        "receive_message",
        socket_payload,
        room=f"user:{friend_id}",
    )
    return jsonify(
        {
            "conversation_id": summary.conversation_id,
            "conversation_type": summary.conversation_type,
            "receiver_id": summary.receiver_id,
            "receiver_display_name": summary.display_name,
            "conversation_img_url": summary.conversation_img_url,
            "message_info": {
                "message_id": str(started.message.message_id),
                "sender_id": started.message.sender_id,
                "sender_display_name": sender_display_name,
                "message_type": "text",
                "content": started.message.content,
                "created_at": _format_utc_iso(started.message.created_at),
            }
        }
    ), 201