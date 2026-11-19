from flask import Blueprint, send_from_directory, session, redirect, url_for
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"

# Create Blueprint for Auth routes
users_routes_bp = Blueprint('users_routes', __name__, url_prefix='/')


@users_routes_bp.route('/', methods=['GET'])
def index():
    # if logged in, redirect to app
    if "user_id" in session:
        return redirect(url_for("serve_app"))
    # else, log in
    return send_from_directory(TEMPLATE_DIR, 'login.html')


@users_routes_bp.route('/register', methods=['GET'])
def serve_register_page():
    return send_from_directory(TEMPLATE_DIR, 'register.html')


@users_routes_bp.route('/chat', methods=['GET'])
def serve_app():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return send_from_directory(TEMPLATE_DIR, "chat.html")