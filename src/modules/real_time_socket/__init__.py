from .extensions import socketio

def init_socketio(app):
    socketio.init_app(app, async_mode="threading")

    # Importing the modules runs their @socketio.on decorators.
    # Without these imports, the handlers never exist.
    from .events import connection, messages  # noqa: F401