from flask import Blueprint, request, jsonify, session

from utils import error_response, login_required

messages_bp = Blueprint('messages_bp', __name__, url_prefix='/api/messages')


@messages_bp.route('/', methods=['GET'])
@login_required
def get_messages():
    conversation_id = request.args.get('conversation_id', 0, type=int)
    if not conversation_id:
        return error_response('conversation_id invalid', 400)

    user_id = session.get('user_id')

    before = request.args.get('before', '', type=str)
    if before:
        limit = request.args.get('limit', 0, type=int)
        if limit:
            if not isinstance(limit, int):
                return error_response('limit invalid', 400)
            if limit < 1 or limit > 100:
                return error_response('limit must be between 1 and 100', 400)
        else: # empty limit, default 30
            limit = 30

        # TODO: call service
        # messages, err = get_messages_service(user_id, conversation_id, before=before, limit=limit)
    
    else: # no before set, default newest messages
        # TODO: call service
        # messages, err = get_messags_service(user_id, conversation_id)
        pass

    # if err:
    #   match err:
    #       case 'Conversation not found':
    #           return error_response(err, 404)
    #       case 'Before not valid' | 'Before not found':
    #           return error_response(err, 400)
    #       case _:
    #           return error_response('Internal server error', 500)

    # hardcoded response
    messages = [
        {
            "message_id": "5f1c2a9e-8b7d-11ef-9c3a-0242ac120002",
            "sender_id": 7,
            "sender_display_name": "Jane Doe",
            "message_type": "text",
            "content": "See you tomorrow!",
            "created_at": "2026-11-16T14:20:00Z"
        },
        {
            "message_id": "4e0b19d8-8b7d-11ef-8a2b-0242ac120002",
            "sender_id": 1,
            "sender_display_name": "John Doe",
            "message_type": "text",
            "content": "Sounds good, what time?",
            "created_at": "2026-11-16T14:18:00Z"
        }
    ]

    return jsonify(messages), 200