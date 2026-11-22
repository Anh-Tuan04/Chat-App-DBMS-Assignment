from flask import session
from ..extensions import socketio
from modules.services.container import get_services


def _error(message):
    # The dict returned by a Socket.IO handler is the ack the client's emitWithAck receives.
    # Never emit 'error' + bare return: the client then gets undefined and shows "server did not respond".
    return {'status': 'error', 'message': message}


def _iso(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


@socketio.on('send_message')
def on_message(data):
    """
    data (sent by the client):
    {
        "sender_info": { "username": "johnny", "display_name": "Johnny Smith", "avatar_url": null },  # display only
        "conversation_id": "3",
        "message": "Hello"
    }

    receive_message (sent to the other members' rooms "user:{id}"):
    {
        "sender_info": { "user_id": 12, "username": "...", "display_name": "...", "avatar_url": null },
        "conversation_id": "3",
        "message": "Hello",
        "message_id": "1354263578912345678",
        "created_at": "2026-11-19T05:20:00Z"
    }

    ack: { "status": "success", "message": "...", "message_id": "...", "created_at": "..." }
         { "status": "error", "message": "..." }
    """
    if not isinstance(data, dict):
        return _error('Data must be a json object')

    # The sender comes from the session cookie, never from the client payload
    user_id = session.get('user_id')
    if not user_id:
        return _error('Not logged in')

    raw_conversation_id = data.get('conversation_id')
    text = data.get('message')
    if raw_conversation_id in (None, ''):
        return _error('conversation_id is required')
    if not isinstance(text, str) or not text.strip():
        return _error('message is required')
    try:
        conversation_id = int(raw_conversation_id)   # arrives as a string from dataset
    except (TypeError, ValueError):
        return _error('conversation_id must be an integer')

    client_info = data.get('sender_info')
    if not isinstance(client_info, dict):
        client_info = {}
    username = client_info.get('username') or ''
    sender_info = {
        'user_id': user_id,
        'username': username,
        'display_name': client_info.get('display_name') or username or f'User {user_id}',
        'avatar_url': client_info.get('avatar_url'),
    }

    services = get_services()

    conversation, err = services.conversations.get_for_member(conversation_id, user_id)
    if err or conversation is None:
        return _error(err or 'Internal server error')

    message, err = services.messages.send_message(user_id, conversation_id, text)
    if err or message is None:
        return _error(err or 'Internal server error')

    created_at = _iso(message.created_at)
    outgoing = {
        'sender_info': sender_info,
        'conversation_id': str(conversation_id),
        'message': text,
        'message_id': str(message.message_id),   # must be string
        'created_at': created_at,                # must be string
    }

    # Rooms are named "user:{id}" in events/connection.py
    if conversation.type == 'direct':
        receiver_id = conversation.other_member(int(user_id))
        socketio.emit('receive_message', outgoing, room=f"user:{receiver_id}")
    elif conversation.type == 'group':
        members, err = services.conversations.list_members(user_id, conversation_id, limit=100)
        if err or members is None:
            # The message is saved already; report it instead of failing silently
            return _error(f'Message saved but not delivered: {err}')
        for member in members:
            if member['user_id'] == user_id:
                continue
            socketio.emit('receive_message', outgoing, room=f"user:{member['user_id']}")
    else:
        return _error(f'Unknown conversation type: {conversation.type}')
    print(f"User {user_id} sent to user {receiver_id} message \"{text}\"" if conversation.type == 'direct' else f"User {user_id} sent to group {conversation_id} message \"{text}\"")

    return {
        'status': 'success',
        'message': 'Message sent successfully',
        'message_id': str(message.message_id),
        'created_at': created_at,
    }
