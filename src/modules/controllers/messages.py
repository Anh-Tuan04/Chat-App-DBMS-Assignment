from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, session

from utils import error_response, login_required
from modules.services.container import get_services
messages_bp = Blueprint('messages_bp', __name__, url_prefix='/api/messages')


def _format_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@messages_bp.route('/', methods=['GET'])
@login_required
def get_messages():
    conversation_id = request.args.get('conversation_id', 0, type=int)
    if not conversation_id:
        return error_response('conversation_id invalid', 400)

    user_id = session.get('user_id')

    # limit: default 30, 1..100
    limit = request.args.get('limit', 0, type=int) or 30
    if limit < 1 or limit > 100:
        return error_response('limit must be between 1 and 100', 400)

    # before: id of the oldest message already on screen (the service wants an int)
    before_raw = request.args.get('before', '', type=str)
    before_id = None
    if before_raw:
        try:
            before_id = int(before_raw)
        except ValueError:
            return error_response('Before not valid', 400)

    page, err = get_services().messages.list_messages(user_id, conversation_id, limit, before_id)

    if err or page is None:
        match err:
            case 'Conversation not found':
                return error_response(err, 404)
            case 'Not a member of this conversation':
                return error_response(err, 403)
            case 'Before not valid' | 'Before not found':
                return error_response(err, 400)
            case _:
                return error_response('Internal server error', 500)

    # The service returns a MessagePage (items + next_cursor); the API returns a plain array,
    # newest first, with the sender's display name added.
    names = get_services().users.get_display_names({m.sender_id for m in page.items})
    return jsonify([
        {
            "message_id": str(m.message_id),
            "sender_id": m.sender_id,
            "sender_display_name": names.get(m.sender_id) or str(m.sender_id),
            "message_type": "text",
            "content": m.content,
            "created_at": _format_utc_iso(m.created_at),
        }
        for m in page.items
    ]), 200