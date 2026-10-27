import eventlet
eventlet.monkey_patch()


from flask_socketio import SocketIO, join_room, leave_room, emit
import functools
import os
import secrets

import grpc
from flask import Flask, jsonify, redirect, request, send_file, session, url_for

import cassandra_handler_pb2
import cassandra_handler_pb2_grpc
import mysql_handler_pb2
import mysql_handler_pb2_grpc

app = Flask(__name__)

# Signs the session cookie. Set SECRET_KEY in the environment for anything beyond
# testing; with the random fallback, everyone is logged out when the server restarts.
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Largest request body Flask will read, in bytes; anything bigger gets a 413.
# Raise it (or override it per request) when file uploads are added.
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024
socketio = SocketIO(app, cors_allowed_origins="*")

# Upper bounds for text sent by the client
MAX_USERNAME_LENGTH = 255
MAX_PASSWORD_LENGTH = 1024
MAX_MESSAGE_LENGTH = 4000


class MySQLServiceUnavailable(Exception):
    """Raised when the MySQL microservice can't be reached."""


class CassandraServiceUnavailable(Exception):
    """Raied when the Cassandra microservice can't be reached."""


# gRPC channels (and the stubs built on them) are thread-safe and meant to be
# shared, so they are created once here instead of once per request. Channels
# connect lazily, so the handlers don't need to be up when this file is loaded.
# mysql_channel = grpc.insecure_channel('localhost:50052')
# mysql_stub = mysql_handler_pb2_grpc.MySQLHandlerStub(mysql_channel)

# cassandra_channel = grpc.insecure_channel('localhost:50051')
# cassandra_stub = cassandra_handler_pb2_grpc.CassandraHandlerStub(cassandra_channel)


def authenticate(username, password):
    """Ask the MySQL handler whether these credentials are valid.

    Returns dict {'user_id': int, 'username': str} if valid, else None. 
    Raises MySQLServiceUnavailable if the service is down.
    """
    # TODO: implement call to MySQL handler
    try:
        response = mysql_stub.Login(
            mysql_handler_pb2.LoginRequest(username=username, password=password),
            timeout=5)    # don't let a hung MySQL handler block the request
        if response.ok:
            return {
                'user_id': response.user_id,
                'username': username
            }
        return None
    except grpc.RpcError as err:
        raise MySQLServiceUnavailable() from err


def _require_login(view, on_denied):
    """Decorator for login gating."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return on_denied()
        return view(*args, **kwargs)
    return wrapped


def login_required(view):
    """For pages: visitors without a session are sent to the login page."""
    return _require_login(view, lambda: redirect(url_for('index')))


def api_login_required(view):
    """For JSON endpoints: answer 401, which the client JS turns into a redirect."""
    return _require_login(view, lambda: ('', 401))


@app.route('/')
def index():
    return send_file('login.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    username = data.get('username', '')
    password = data.get('password', '')
    if not (isinstance(username, str) and isinstance(password, str)
            and username and password):
        return '', 400     # missing or malformed credentials
    if len(username) > MAX_USERNAME_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        return '', 400     # credentials too long

    # try:
    #     user = authenticate(username, password)
    # except MySQLServiceUnavailable:
    #     return '', 503     # MySQL handler unavailable

    # if user is None:
    #     return '', 401     # invalid credentials

    # Remember who this browser is, so /app can check it later
    # session['user_id'] = user['user_id']
    if not (username == "test" and password == "test"):
        return '', 401     # invalid credentials
    return jsonify(redirect=url_for('message_app')), 200


@app.route('/app')
# @login_required
def message_app():
    return send_file('message.html')


@app.route('/messages', methods=['POST'])
@api_login_required
def handle_incoming_message():

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return '', 400     # body is not a JSON object
    content = data.get('content')
    if not isinstance(content, str) or not content.strip():
        return '', 400     # missing or blank message
    if len(content) > MAX_MESSAGE_LENGTH:
        return '', 400     # message too long

    print(f'Received message, content: \n', data)

    # Send request to handler
    # try:
    #     response = cassandra_stub.AddMessage(cassandra_handler_pb2.AddMessageRequest(
    #         senderID=session['user_id'],
    #         receiverID=112233,
    #         content=content
    #     ))
    #     if (response.ok):
    #         print("Client received message successfully")
    #         return '', 204

    #     # The handler was reached but failed to store the message
    #     print(f'error: {response.err}')
    #     return '', 500
    # except grpc.RpcError:
    #     return '', 503

# SocketIO
@socketio.on('connect')
def on_connect():
    print(f"Client connected!")



@socketio.on('join')
def on_join(data):
    join_room(data['user_name'])
    emit('connected', {'content': f"{data['user_name']} has entered the room."}, to=data['user_name'])

@socketio.on('leave')
def on_leave(data):
    username = data.get('username', 'Unknown')
    leave_room(username)
    emit('disconnected', {'content': f"{username} has left the room."}, namespace='/chat', to=data['user_name'])

@socketio.on('message')
def handle_message(data):
    print(f"Received message: {data['content']}, sender: {data.get('sender', 'Unknown')}")
    emit('message', {'content': data['content'], 'sender': data.get('sender', 'Unknown')}, to='test')



background_worker_counter = 0
def background_worker():
    global background_worker_counter
    while True:
        socketio.sleep(2)
        background_worker_counter += 1
        socketio.emit('message', {'content': f"Warning you {background_worker_counter} time(s)!", 'sender': 'partner'}, to='test')

if __name__ == '__main__':
    socketio.start_background_task(background_worker)
    socketio.run(app, host='localhost', port=5000, debug=True)