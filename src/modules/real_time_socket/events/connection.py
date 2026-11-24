# modules/real_time_socket/events/connection.py
from flask import session, request
from flask_socketio import join_room, disconnect
from ..extensions import socketio
from flask_socketio import ConnectionRefusedError

@socketio.on("connect")
def on_connect():
    user_id = session.get("user_id")   # the session cookie is sent in the handshake
    if user_id is None:
        raise ConnectionRefusedError("unauthorized")
    join_room(f"user:{user_id}")       # personal room for notifications
    print(f"User {user_id} connected. SID: {request.sid}")
    # optionally join each conversation room the user belongs to