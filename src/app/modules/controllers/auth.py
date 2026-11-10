from flask import Blueprint, request, jsonify, send_from_directory
from pathlib import Path
import datetime

# TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth/')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Create a new user account
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        body = {}

    display_name = body.get('display_name', '')
    username = body.get('username', '')
    password = body.get('password', '')

    if not (display_name and username and password):
        return jsonify({'message': 'Missing field'}), 400

    if not (isinstance(display_name, str) 
            and isinstance(username, str)
            and isinstance(password, str)):
        return jsonify({'message': 'Wrong input type'}), 400

    if len(display_name) > 50:
        return jsonify({'message': 'Display name too long'}), 400

    if len(username) < 3:
        return jsonify({'message': 'Username too short'}), 400

    if len(password) < 6:
        return jsonify({'message': 'Password too short'}), 400

    if len(password) > 128:
        return jsonify({'message': 'Password too long'}), 400

    # TODO: implement register service call
    # still a hardcoded response for testing
    user = {
        'user_id': 1,
        'username': username,
        'display_name': display_name,
        'created_at': datetime.datetime.now().replace(microsecond=0).isoformat()
    }

    return jsonify(user), 200
