from flask_socketio import SocketIO

socketio = SocketIO()

def init_socketio(app):
    socketio.init_app(app, cors_allowed_origins=[])  # same-origin: no CORS needed
    from .events import connection, messages, notifications  # registers handlers