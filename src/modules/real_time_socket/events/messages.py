from flask import session
from flask_socketio import emit
from ..extensions import socketio
from modules.services.container import get_services


def _emit_error(message, data=None):
    """Tell ONLY the sending socket that its message failed (emit() inside a handler goes
    back to request.sid). The original text and conversation_id are echoed so the client
    can put the text back into the composer."""
    data = data if isinstance(data, dict) else {}
    emit('send_message_error', {
        'status': 'error',
        'message': message,
        'conversation_id': str(data.get('conversation_id') or ''),
        'text': data.get('message') if isinstance(data.get('message'), str) else '',
    })


def _iso(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


@socketio.on('send_message')
def on_message(data):
    """
    data (sent by the client, plain emit, no ack):
    {
        "sender_info": { "username": "johnny", "display_name": "Johnny Smith", "avatar_url": null },  # display only
        "conversation_id": "3",
        "message": "Hello"
    }

    receive_message (sent to EVERY member's room "user:{id}", the sender included, so the
    sender's tabs show the message only once the server has saved it):
    {
        "sender_info": { "user_id": 12, "username": "...", "display_name": "...", "avatar_url": null },
        "conversation_id": "3",
        "message": "Hello",
        "message_id": "1354263578912345678",
        "created_at": "2026-11-19T05:20:00Z"
    }

    send_message_error (sent only to the sending socket):
    { "status": "error", "message": "...", "conversation_id": "3", "text": "Hello" }
    """
    if not isinstance(data, dict):
        return _emit_error('Data must be a json object')

    # The sender comes from the session cookie, never from the client payload
    user_id = session.get('user_id')
    if not user_id:
        return _emit_error('Not logged in', data)

    raw_conversation_id = data.get('conversation_id')
    text = data.get('message')
    if raw_conversation_id in (None, ''):
        return _emit_error('conversation_id is required', data)
    if not isinstance(text, str) or not text.strip():
        return _emit_error('message is required', data)
    try:
        conversation_id = int(raw_conversation_id)   # arrives as a string from dataset
    except (TypeError, ValueError):
        return _emit_error('conversation_id must be an integer', data)

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
        return _emit_error(err or 'Internal server error', data)

    # Who receives it, the sender included
    if conversation.type == 'direct':
        member_ids = [int(user_id), conversation.other_member(int(user_id))]
    elif conversation.type == 'group':
        members, err = services.conversations.list_members(user_id, conversation_id, limit=100)
        if err or members is None:
            return _emit_error(err or 'Internal server error', data)
        member_ids = [member['user_id'] for member in members]
        if int(user_id) not in member_ids:
            member_ids.append(int(user_id))
    else:
        return _emit_error(f'Unknown conversation type: {conversation.type}', data)

    message, err = services.messages.send_message(user_id, conversation_id, text)
    if err or message is None:
        return _emit_error(err or 'Internal server error', data)

    outgoing = {
        'sender_info': sender_info,
        'conversation_id': str(conversation_id),
        'message': text,
        'message_id': str(message.message_id),   # must be string
        'created_at': _iso(message.created_at),  # must be string
    }

    # Rooms are named "user:{id}" in events/connection.py
    for member_id in member_ids:
        socketio.emit('receive_message', outgoing, room=f"user:{member_id}")
    print(f"User {user_id} sent to conversation {conversation_id} ({conversation.type}) message \"{text}\"")
