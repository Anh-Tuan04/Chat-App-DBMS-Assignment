from ..extensions import socketio


def emit_delete_message_for_me(user_id: int, conversation_id: int, message_id: int) -> None:
    """Tell every tab of ONE user that a message is now hidden for them ("delete for me").
    Other members are not told: the message still exists for them.

    Emitted 'message_deleted_for_me' to room "user:{user_id}":
        {
            "conversation_id": "3",
            "message_id": "1354263578912345678"     # string: too big for a JS number
        }
    """
    socketio.emit(
        'message_deleted_for_me',
        {
            'conversation_id': str(conversation_id),
            'message_id': str(message_id),
        },
        room=f"user:{user_id}",
    )


def emit_recall_message(
    member_ids,
    conversation_id: int,
    message_id: int,
    recalled_by: int,
    latest_message: dict | None,
    has_latest_message: bool = True,
) -> None:
    """Tell EVERY member (the sender included, for their other tabs) that a message was
    deleted for everyone.

    Emitted 'message_recalled' to each room "user:{id}":
        {
            "conversation_id": "3",
            "message_id": "1354263578912345678",
            "recalled_by": 12,
            "latest_message": {                     # the sidebar preview after the delete
                "message_id": "1354263578900000000",
                "sender_id": 7,
                "content": "See you tomorrow!",
                "created_at": "2026-11-19T05:18:00Z"
            }                                       # null: the conversation has no message left
        }
    `latest_message` is left out of the payload when the server could not read it
    (has_latest_message=False). The client then keeps its preview as it is.
    """
    payload = {
        'conversation_id': str(conversation_id),
        'message_id': str(message_id),
        'recalled_by': int(recalled_by),
    }
    if has_latest_message:
        payload['latest_message'] = latest_message

    for member_id in member_ids:
        socketio.emit('message_recalled', payload, room=f"user:{member_id}")
