import uuid

from flask import session
from ..extensions import socketio
from modules.services import messages as message_service
from datetime import datetime, timezone

def format_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

message_id = 0

@socketio.on('send_message')
def on_message(data):
    """
    data: 
    {
        sender_info: {
            "user_id": 12,
            "username": "johnny",
            "display_name": "Johnny Smith",
            "avatar_url": null
        },
        "conversation_id": "conv123",
        "message": "Hello, this is a test message."
    }

    response: 
    {
        sender_info: {
            "user_id": 12,
            "username": "johnny",
            "display_name": "Johnny Smith",
            "avatar_url": null
        },
        "conversation_id": "conv123",
        "message": "Hello, this is a test message.",
        message_id: "1354263578912345678",
        created_at: "2026-11-19T05:20:00Z"
    }

    """
    if not data:
        socketio.emit('error', {'message': 'No data provided'})
        return
    if not isinstance(data, dict):
        socketio.emit('error', {'message': 'Data must be a json object'})
        return
    if not data.get('sender_info'):
        socketio.emit('error', {'message': 'sender_info is required'})
        return
    if not data.get('sender_info').get('user_id'):
        socketio.emit('error', {'message': 'sender_info.user_id is required'})
        return
    if not data.get('sender_info').get('username'):
        socketio.emit('error', {'message': 'sender_info\'s username is required'})
        return
    if not data.get('sender_info').get('display_name'):
        socketio.emit('error', {'message': 'sender_info\'s display_name is required'})
        return
    
    
    if not data.get('sender_info'):
        socketio.emit('error', {'message': 'sender_info is required'})
        return
    if not data.get('conversation_id'):
        socketio.emit('error', {'message': 'conversation_id is required'})
        return
    if not data.get('message'):
        socketio.emit('error', {'message': 'message is required'})
        return

    sender_id = data['sender_info']
    conversation_id = data['conversation_id']
    message = data['message']
    receiver_ids, err = ([], None)   # Call the service to query the database to get the list of receiver_ids based on conversation_id (query channels and channel_members table????)

    if err:
        socketio.emit('error', {'message': f'{err}'})
        return
    
    # Call service to save the message to the database
    # (message_id, conversation_id, sender_id, content, created_at), err = ((None, None, None, None, None), err)

    if err:
        socketio.emit('error', {'message': f'{err}'})
        return
    
    # data.add('message_id', message_id.__str__())  # must be string
    # data.add('created_at', created_at.__str__())  # must be string
    # for receiver_id in receiver_ids:
    #     socketio.emit('receive_message', data, room=receiver_id, include_self=False)



    # Place holder message_id and created_at for now
    message_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    data["message_id"] = message_id
    data["created_at"] = created_at
    

    if data['sender_info']['user_id'] == 2:
        receiver_id = 3
    elif data['sender_info']['user_id'] == 3:
        receiver_id = 2
    print(f"User {sender_id} sent a message to User {receiver_id}: {message}")
    socketio.emit('receive_message', data, room=f"user:{receiver_id}", include_self=False)



    return {
        'status': 'success', 
        'message': 'Message sent successfully',
        "message_id": message_id,
        "created_at": created_at
    }