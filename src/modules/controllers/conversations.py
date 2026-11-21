from flask import Blueprint, request, jsonify, session

from utils import error_response, login_required

conversations_bp = Blueprint('conversation_bp', __name__, url_prefix='/api/conversations')


@conversations_bp.route('/', methods=['GET'])
@login_required
def get_conversations():
    user_id = session.get('user_id')

    # TODO: call service
    # conversations, err = get_conversations_service(user_id)
    # if err:
    #   return error_response('Internal server error', 500)

    # hardcoded response
    conversations = [
        {
            "conversation_id": 1,
            "conversation_type": "direct",
            "receiver_id": 7,
            "display_name": "Jane Doe",
            "conversation_img_url": "",
            "latest_message": {
                "message_id": "5f1c2a9e-8b7d-11ef-9c3a-0242ac120002",
                "sender_id": 7,
                "sender_display_name": "Jane Doe",
                "message_type": "text",
                "content": "See you tomorrow!",
                "created_at": "2026-11-16T14:20:00Z"
            },
            "unread_count": 3
        },
        {
            "conversation_id": 2,
            "conversation_type": "group",
            "receiver_id": "",
            "display_name": "Project Team",
            "conversation_img_url": "",
            "latest_message": "",
            "unread_count": 0
        }
    ]

    return jsonify(conversations), 200


@conversations_bp.route('/new-group', methods=['POST'])
@login_required
def create_group():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error_response("Body must be a JSON object", 400)

    group_name = body.get('group_name', '')
    member_ids = body.get('member_ids', [])

    if not group_name or len(group_name.strip()) == 0:
        return error_response('Group name must not be empty', 400)
    if len(group_name) > 100:
        return error_response('Group name too long', 400)

    if not member_ids:
        return error_response('Must include at least one member', 400)
    if len(member_ids) > 99:
        return error_response('Too many members', 400)

    user_id = session.get('user_id')

    if user_id in member_ids:
        return error_response('Must not contain self', 400)

    # TODO: call service
    # group, err = create_group_service(user_id, group_nam, member_ids)
    # if err:
    #   match err:
    #       case 'Member not found':
    #           return error_response(err, 404)
    #       case _:
    #           return ('Internal server error', 500)

    # hardcoded response
    group = {
        "conversation_id": 4,
        "conversation_type": "group",
        "receiver_id": '',
        "receiver_display_name": "Project Team",
        "conversation_img_url": ''
    }

    return jsonify(group), 200


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
    if not message or len(message.strip()) == 0:
        return error_response('message must not be empty', 400)
    if len(message) > 2000:
        return error_response('message too long', 400)

    # TODO: call service
    # conversation, err = create_conversation_service(user_id, friend_id, message)
    # if err:
    #   match err:
    #       case 'Conversation already exists':
    #           return error_response(err, 409)
    #       case 'User not found':
    #           return error_response(err, 404)
    #       case _:
    #           return error_response('Internal server error', 500)

    # hardcoded response
    conversation = {
        "conversation_id": 3,
        "conversation_type": "direct",
        "receiver_id": 7,
        "receiver_display_name": "Jane Doe",
        "conversation_img_url": ""
    }

    return jsonify(conversation), 200