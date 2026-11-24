from flask import Blueprint, jsonify, request, session

from ..services.container import get_services
from utils import error_response, login_required

notifications_bp = Blueprint('notifications_bp', __name__, url_prefix='/api/notifications')


@notifications_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    user_id = session.get('user_id')

    before_raw = request.args.get('before')
    if before_raw is None:
        before_notification_id = None
    else:
        try:
            before_notification_id = int(before_raw)
        except ValueError:
            return error_response('before is not a valid notification ID', 400)
        if before_notification_id <= 0:
            return error_response('before is not a valid notification ID', 400)

    limit_raw = request.args.get('limit')
    if limit_raw is None:
        limit = 30
    else:
        try:
            limit = int(limit_raw)
        except ValueError:
            return error_response('limit must be between 1 and 100', 400)
        if not 1 <= limit <= 100:
            return error_response('limit must be between 1 and 100', 400)

    services = get_services()
    # notifications = [...]  # Previous hardcoded response.
    notifications, err = services.notifications.list_for_user_payload(
        user_id, limit=limit, before_notification_id=before_notification_id
    )
    if err:
        return error_response('Internal server error', 500)
    if notifications is None:
        return error_response('Internal server error', 500)

    return jsonify(notifications), 200
