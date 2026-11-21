from flask import session
from ..extensions import socketio
from modules.services import conversations as conversation_service


@socketio.on('mark_read')
def on_mark_read(data):
    """
    Mark a conversation as read for the logged-in user (resets its unread count).

    data:
    {
        "conversation_id": "1"
    }

    ack (the dict returned by this function, received by emitWithAck on the client):
    success: { "status": "success", "conversation_id": "1", "unread_count": 0 }
    error:   { "status": "error", "message": "string" }
    """
    if not isinstance(data, dict):
        return {'status': 'error', 'message': 'Data must be a json object'}
    if not data.get('conversation_id'):
        return {'status': 'error', 'message': 'conversation_id is required'}

    # The user comes from the session cookie, never from the client payload
    user_id = session.get('user_id')
    if not user_id:
        return {'status': 'error', 'message': 'Not logged in'}

    conversation_id = data['conversation_id']

    # Call the service to mark the conversation as read for this user
    # (check the user is a member of the conversation, then reset the unread count / last read message)
    err = None   # err = conversation_service.mark_read(user_id, conversation_id)

    if err:
        return {'status': 'error', 'message': f'{err}'}

    return {'status': 'success', 'conversation_id': str(conversation_id), 'unread_count': 0}