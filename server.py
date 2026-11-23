import os
import sys
from pathlib import Path

from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException

import logging

# logging.getLogger("werkzeug").disabled = True
# logging.getLogger("werkzeug").propagate = False

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.utils import SkippableSessionInterface, error_response
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
# templates/ is supposed to stored jinja templates,
# but it is currently used for plain html

# Imports from controllers
from src.modules.controllers.auth import auth_bp
from src.modules.controllers.conversations import conversations_bp
from src.modules.controllers.messages import messages_bp
from src.modules.controllers.notifications import notifications_bp
from src.modules.controllers.relationships import relationships_bp, blocks_bp
from src.modules.controllers.users import users_bp
from src.users.routes import users_routes_bp

from src.modules.real_time_socket import init_socketio
from src.modules.real_time_socket.extensions import socketio
from src.modules.real_time_socket.emitters.notifications import emit_notification
from src.modules.services.container import init_app_services


def create_app(config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path='/static',
        # template_folder=str(TEMPLATES_DIR)
    )
    @app.before_request
    def print_request():
        print(f"Request: {request.method} {request.path}", flush=True)


    @app.after_request
    def print_response(response):
        print(
            f"Response: {request.method} {request.path} -> {response.status_code}",
            flush=True,
        )
        return response

    # new key every startup to force new login, unreliable
    app.config["SECRET_KEY"] = os.urandom(32) 
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if config:
        app.config.update(config)

    app.session_interface = SkippableSessionInterface()
    services = init_app_services(app)
    # Push each stored notification to the receiver's socket room ("user:{id}"), so the bell
    # badge updates in real time. The service only knows the callable, never the socket code.
    services.notifications.set_publisher(emit_notification)

    # Force flask's abort to also not set cookie
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return error_response(e.description, e.code)

    # Register controller blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(relationships_bp)
    app.register_blueprint(blocks_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(users_routes_bp)

    init_socketio(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:5000"}},
        supports_credentials=True,
    )
    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True,
    )