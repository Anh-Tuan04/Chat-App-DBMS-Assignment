from flask import Blueprint, request, jsonify, session

from ..services.container import get_services
from utils import error_response, login_required

notifications_bp = Blueprint('notifications_bp', __name__, url_prefix='/api/notifications')


@notifications_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    """
    Get all unresolved notifications.
    """
    user_id = session.get('user_id')

    before = request.args.get('before', '', type=str)
    if before:
        limit = request.args.get('limit', 0, type=int)
        if limit:
            if not isinstance(limit, int):
                return error_response('limit invalid', 400)
            if limit < 1 or limit > 100:
                return error_response('limit must be between 1 and 100', 400)
        else: # empty limit, default 30
            limit = 30

        # TODO: call service
        # notifications, err = get_notifications_service(user_id, before=before, limit=limit)
    
    else: # no before set, default newest messages
        # TODO: call service
        # notifications, err = get_notifications_service(user_id)
        pass

    # if err:
    #   return error_response('Internal server error', 500)

    # hardcoded response
    notifications = [
        {
            "notification_id": "1789432156738291900",
            "notification_type": "friend_request",
            "is_read": False,
            "created_at": "2026-11-19T05:20:00Z",
            "payload": {
                "actor": {
                    "user_id": 7,
                    "username": "jane_doe",
                    "display_name": "Jane Doe",
                    "avatar_url": ""
                }
            }
        },
        {
            "notification_id": "1789432156738291850",
            "notification_type": "friend_accepted",
            "is_read": True,
            "created_at": "2026-11-18T10:02:00Z",
            "payload": {
                "actor": {
                    "user_id": 12,
                    "username": "johnny",
                    "display_name": "Johnny Smith",
                    "avatar_url": ""
                }
            }
        },
        {
            "notification_id": "1789432156738291800",
            "notification_type": "group_added",
            "is_read": False,
            "created_at": "2026-11-17T08:30:00Z",
            "payload": {
                "actor": {
                    "user_id": 21,
                    "username": "mike99",
                    "display_name": "Mike",
                    "avatar_url": ""
                },
                "conversation_id": 4,
                "group_name": "Project Team"
            }
        }
    ]

    return jsonify(notifications), 200