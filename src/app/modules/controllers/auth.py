from flask import Blueprint, request, jsonify, session
import datetime

from ..services.auth import login_service, logout_service, register_service
from ...utils import error_response, login_required

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth/')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Create a new user account
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error_response("Body must be a JSON object", 400)

    display_name = body.get('display_name', '')
    username = body.get('username', '')
    password = body.get('password', '')

    # TODO: sanitize

    if not (display_name and username and password):
        return error_response('Missing field', 400)

    if not (isinstance(display_name, str) 
            and isinstance(username, str)
            and isinstance(password, str)):
        return error_response('Wrong input type', 400)

    if len(display_name) > 50:
        return error_response('Display name too long', 400)

    if len(username) < 3:
        return error_response('Username too short', 400)

    if len(password) < 6:
        return error_response('Password too short', 400)

    if len(password) > 128:
        return error_response('Password too long', 400)

    # TODO: implement register service call
    user, err = register_service(username, password, display_name)
    if err:
      match err:
          case "Username already in use":
              return error_response(err, 409)
          case _:
              return error_response("Internal server error", 500)

    # still a hardcoded response for testing
    # user = {
    #     'user_id': 1,
    #     'username': username,
    #     'display_name': display_name,
    #     'created_at': datetime.datetime.now().replace(microsecond=0).isoformat()
    # }

    return jsonify(user), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Call auth service and return the user's info
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error_response("Body must be a JSON object", 400)

    username = body.get('username', '')
    password = body.get('password', '')

    if not (username and password):
        return error_response('Missing field', 400)

    if not (isinstance(username, str) and isinstance(password, str)):
        return error_response("Wrong input type", 400)
    # TODO: sanitize, type check, constraint enforce

    # TODO: call auth service
    user, err = login_service(username, password)
    if err:
      match err:
          case "username or password incorrect":
              return error_response(err, 401)
          case _:
              return error_response("Internal server error", 500)

    # hardcoded response for now
    # user = {
    #     'user_id': 1,
    #     'username': username,
    #     'display_name': 'Test user',  
    #     'avatar_url': ''
    # }

    session["user_id"] = user.get("user_id")
    return jsonify(user), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    user_id = session.get("user_id")

    # TODO: call service
    err = logout_service(user_id)
    if err:
      return error_response("Internal server error", 500)

    session.clear()
    return '', 204