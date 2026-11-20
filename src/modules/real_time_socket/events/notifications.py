from flask import session
from ..extensions import socketio
from modules.services import notifications

@socketio.on('read_notification')
def handle_read_notification(data):
    notification_id = data.get('notification_id')
    if not notification_id:
        socketio.emit('error', {'message': 'notification_id is required'})
        return

    user_id = session.get('user_id')
    if not user_id:
        socketio.emit('error', {'message': 'user_id is required'})
        return

    _, err = notifications.mark_as_read(notification_id, user_id)
    if err:
        socketio.emit('error', {'message': str(err)})
        return

    socketio.emit('notification_read', {'status': 'success', 'notification_id': notification_id})