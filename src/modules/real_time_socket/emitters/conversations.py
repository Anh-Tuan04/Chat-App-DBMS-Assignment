from ..extensions import socketio


def build_conversation_views(conversation, member_ids, profiles) -> dict:
    """What the sidebar row of `conversation` looks like for each member.

    Same shape as one item of GET /api/conversations (without latest_message and
    unread_count), so a client that does not have the row yet can draw it without
    fetching the whole list again:
        {
            "conversation_id": "3",
            "conversation_type": "direct" | "group",
            "receiver_id": 7,                 # the OTHER person of a direct chat, null for a group
            "display_name": "Jane Doe",       # the other person's name, or the group name
            "conversation_img_url": null      # the other person's avatar, null for a group
        }

    Args:
        conversation: modules.repositories.conversations.Conversation
        member_ids: every member who will receive the event
        profiles: {user_id: {"display_name", "avatar_url", ...}} (UserService.get_public_profiles)
    Returns:
        {member_id: view}. A direct chat differs per member; a group is the same for all.
    """
    views = {}
    for member_id in member_ids:
        if conversation.type == 'direct':
            other_id = conversation.other_member(int(member_id))
            other = profiles.get(other_id) or {}
            views[member_id] = {
                'conversation_id': str(conversation.conversation_id),
                'conversation_type': 'direct',
                'receiver_id': other_id,
                'display_name': other.get('display_name') or f'User {other_id}',
                'conversation_img_url': other.get('avatar_url'),
            }
        else:
            views[member_id] = {
                'conversation_id': str(conversation.conversation_id),
                'conversation_type': 'group',
                'receiver_id': None,
                'display_name': conversation.name or 'Group',
                'conversation_img_url': None,
            }
    return views


def emit_message_to_members(message_payload: dict, views: dict) -> None:
    """Emit 'receive_message' to each member's room "user:{id}" (see events/connection.py),
    adding that member's own `conversation` view to the payload.

    Emitted payload:
        {
            "sender_info": { "user_id": 12, "username": "...", "display_name": "...", "avatar_url": null },
            "conversation_id": "3",
            "message": "Hello",
            "message_id": "1354263578912345678",
            "created_at": "2026-11-19T05:20:00Z",
            "conversation": { ...see build_conversation_views... }
        }
    """
    for member_id, view in views.items():
        socketio.emit(
            'receive_message',
            {**message_payload, 'conversation': view},
            room=f"user:{member_id}",
        )
