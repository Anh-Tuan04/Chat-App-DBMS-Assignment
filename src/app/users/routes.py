from flask import Blueprint, send_from_directory
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"

# Create Blueprint for Auth routes
users_routes_bp = Blueprint('users_routes', __name__, url_prefix='/')


@users_routes_bp.route('/', methods=['GET'])
def index():
    # if logged in, redirect to app

    # else, redirect to log in

    return send_from_directory(TEMPLATE_DIR, 'login.html')