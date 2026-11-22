from .extensions import socketio

def init_socketio(app):
    socketio.init_app(app)

    # Importing the modules runs their @socketio.on decorators.
    # Without these imports, the handlers never exist.
    from .events import connection, messages, conversation  # noqa: F401
