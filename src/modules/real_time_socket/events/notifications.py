from flask import session
from ..extensions import socketio
from modules.services.container import get_services


@socketio.on('read_notification')
def on_read_notification(data):
    """
    Mark notifications as read for the logged-in user.

    data:
    { "notification_ids": ["1789432156738291900", "1789432156738291850"] }

    ack (the dict returned here, received by emitWithAck on the client):
    success: { "status": "success", "notification_ids": ["1789432156738291900", ...] }
    error:   { "status": "error", "message": "string" }
    """
    if not isinstance(data, dict):
        return {'status': 'error', 'message': 'Data must be a json object'}

    # The user comes from the session cookie, never from the client payload
    user_id = session.get('user_id')
    if not user_id:
        return {'status': 'error', 'message': 'Not logged in'}

    raw_ids = data.get('notification_ids')
    if not isinstance(raw_ids, list) or not raw_ids or len(raw_ids) > 100:
        return {'status': 'error', 'message': 'notification_ids must be a list of 1 to 100 ids'}
    try:
        notification_ids = [int(raw_id) for raw_id in raw_ids]   # ids arrive as strings
    except (TypeError, ValueError):
        return {'status': 'error', 'message': 'notification_ids must be integers'}

    _, err = get_services().notifications.mark_read(user_id, notification_ids)
    if err:
        return {'status': 'error', 'message': err}

    return {'status': 'success', 'notification_ids': [str(notification_id) for notification_id in notification_ids]}