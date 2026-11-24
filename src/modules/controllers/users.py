from flask import Blueprint, request, jsonify, session

from modules.services.container import get_services
from utils import error_response, login_required

users_bp = Blueprint('users_bp', __name__, url_prefix='/api/users')


@users_bp.route('/search', methods=['GET'])
@login_required
def search_user():
    search_name = request.args.get('username', '', type=str).strip()
    if not search_name:
        return error_response('Search keyword is required', 400)
    if len(search_name) > 50:
        return error_response('Keyword longer than allowed', 400)

    users, err = get_services().users.search(
        search_name, current_user_id=session.get('user_id')
    )
    if err or users is None:
        return error_response('Internal server error', 500)

    return jsonify(users), 200