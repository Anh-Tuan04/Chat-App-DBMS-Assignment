from flask import session
from ..extensions import socketio
from modules.services.container import get_services

# The service clamps the value to the real latest message, so this means "up to the latest".
LATEST_MESSAGE_ID = 2 ** 63 - 1


@socketio.on('mark_read')
def on_mark_read(data):
    """
    Mark a conversation as read for the logged-in user (resets its unread count).

    data:
    {
        "conversation_id": "1",
        "last_message_id": "123"      # optional, default = the latest message
    }

    ack (the dict returned by this function, received by emitWithAck on the client):
    success: { "status": "success", "conversation_id": "1", "unread_count": 0 }
    error:   { "status": "error", "message": "string" }
    """
    if not isinstance(data, dict):
        return {'status': 'error', 'message': 'Data must be a json object'}

    # The user comes from the session cookie, never from the client payload
    user_id = session.get('user_id')
    if not user_id:
        return {'status': 'error', 'message': 'Not logged in'}

    try:
        conversation_id = int(data.get('conversation_id'))
        raw_last = data.get('last_message_id')
        last_message_id = int(raw_last) if raw_last not in (None, '') else LATEST_MESSAGE_ID
    except (TypeError, ValueError):
        return {'status': 'error', 'message': 'conversation_id must be an integer'}

    _, err = get_services().conversations.mark_read(user_id, conversation_id, last_message_id)

    # A conversation without messages has nothing to mark: not an error for the UI
    if err and err != 'No message read':
        return {'status': 'error', 'message': f'{err}'}

    print(f"User {user_id} marked conversation {conversation_id} as read up to message {last_message_id}")

    return {'status': 'success', 'conversation_id': str(conversation_id), 'unread_count': 0}
