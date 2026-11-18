from flask import Blueprint, request, jsonify, session

from ...utils import error_response, login_required

users_bp = Blueprint('users_bp', __name__, url_prefix='/api/users')


@users_bp.route('/search', methods=['GET'])
@login_required
def search_user():
    search_name = request.args.get('username', '', type=str)
    if not search_name:
        return error_response('Search keyword is required', 400)
    if len(search_name) > 50:
        return error_response('Keyword longer than allowed', 400)

    # TODO: call service
    # users, err = search_user_service(search_name)
    # if err:
    #   return error_response('Internal server error', 500)

    # hardcoded response
    users = [
        {
            "user_id": 7,
            "username": "john_doe",
            "display_name": "John Doe",
            "avatar_url": ""
        },
        {
            "user_id": 12,
            "username": "johnny",
            "display_name": "Johnny Smith",
            "avatar_url": ""
        }
    ]

    return jsonify(users), 200