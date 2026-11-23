from ..extensions import socketio

def emit_notification(receiver_id: int, payload: dict):
    """Emit a real-time notification payload to the target user room.

    Args:
        payload: Notification input payload.

    Response payloads (emitted event):
        1. ``friend_request``:
            ```json
            {
                "notification_id": "1789432156738291900",
                "notification_type": "friend_request",
                "is_read": 0,
                "created_at": "2026-11-19T05:20:00Z",
                "payload": {
                    "actor": {
                        "user_id": 7,
                        "username": "jane_doe",
                        "display_name": "Jane Doe",
                        "avatar_url": "https://example.com/avatars/jane.png"
                    }
                }
            }
            ```

        2. ``friend_accepted``:
            ```json
            {
                "notification_id": "1789432156738291850",
                "notification_type": "friend_accepted",
                "is_read": 1,
                "created_at": "2026-11-18T10:02:00Z",
                "payload": {
                    "actor": {
                        "user_id": 12,
                        "username": "johnny",
                        "display_name": "Johnny Smith",
                        "avatar_url": null
                    }
                }
            }
            ```

        3. ``group_added``:
            ```json
            {
                "notification_id": "1789432156738291800",
                "notification_type": "group_added",
                "is_read": 0,
                "created_at": "2026-11-17T08:30:00Z",
                "payload": {
                    "actor": {
                        "user_id": 21,
                        "username": "mike99",
                        "display_name": "Mike",
                        "avatar_url": null
                    },
                    "conversation_id": 4,
                    "group_name": "Project Team"
                }
            }
            ```
    """
    # Rooms are named "user:{id}" in events/connection.py.
    # No include_self=False: this runs inside an HTTP request, where there is no socket id to skip.
    socketio.emit('receive_notification', payload, room=f"user:{receiver_id}")