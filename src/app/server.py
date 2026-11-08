from pathlib import Path
from flask import Flask

BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "static"
# templates/ is supposed to stored jinja templates,
# but it is currently used for plain html
# TEMPLATES_DIR = BASE_DIR / "templates"

# Imports from controllers
# from app.modules.controllers.auth import auth_bp
# from app.modules.controllers.conversations import conversations_bp
# from app.modules.controllers.messages import messages_bp
# from app.modules.controllers.notifications import notifications_bp
# from app.modules.controllers.relationships import relationships_bp
# from app.modules.controllers.users import users_bp
from app.users.routes import users_routes_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path='/static',
        # template_folder=str(TEMPLATES_DIR)
    )

    # Register controller blueprints
    # app.register_blueprint(auth_bp)
    # app.register_blueprint(conversations_bp)
    # app.register_blueprint(messages_bp)
    # app.register_blueprint(notifications_bp)
    # app.register_blueprint(relationships_bp)
    # app.register_blueprint(users_bp)
    app.register_blueprint(users_routes_bp)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)