import os
import sys
from pathlib import Path

from flask import Flask, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils import SkippableSessionInterface, error_response
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
# templates/ is supposed to stored jinja templates,
# but it is currently used for plain html

# Imports from controllers
from modules.controllers.auth import auth_bp
from modules.controllers.conversations import conversations_bp
from modules.controllers.messages import messages_bp
# from app.modules.controllers.notifications import notifications_bp
from modules.controllers.relationships import relationships_bp
from modules.controllers.users import users_bp
from users.routes import users_routes_bp

from modules.real_time_socket import init_socketio
from modules.real_time_socket.extensions import socketio


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path='/static',
        # template_folder=str(TEMPLATES_DIR)
    )
    # @app.before_request
    # def print_request():
    #     print(f"Request: {request.method} {request.path}", flush=True)

    # @app.after_request
    # def print_response(response):
    #     print(
    #         f"Response: {request.method} {request.path} -> {response.status_code}",
    #         flush=True,
    #     )
    #     return response

    # new key every startup to force new login, unreliable
    app.config["SECRET_KEY"] = os.urandom(32) 
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    app.session_interface = SkippableSessionInterface()

    # Force flask's abort to also not set cookie
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return error_response(e.description, e.code)

    # Register controller blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(messages_bp)
    # app.register_blueprint(notifications_bp)
    app.register_blueprint(relationships_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(users_routes_bp)

    init_socketio(app)
    return app


app = create_app()

CORS(
    app,
    resources={r"/api/*": {"origins": "http://localhost:5000"}},
    supports_credentials=True,
)


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True,
    )