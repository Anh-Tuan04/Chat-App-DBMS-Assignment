import os
import secrets

import grpc
from flask import Flask, jsonify, redirect, request, send_file, session, url_for

import auth_pb2
import auth_pb2_grpc
import cassandra_handler_pb2
import cassandra_handler_pb2_grpc

app = Flask(__name__)

# Signs the session cookie. Set SECRET_KEY in the environment for anything beyond
# testing; with the random fallback, everyone is logged out when the server restarts.
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)


class AuthServiceUnavailable(Exception):
    """Raised when the MySQL auth microservice can't be reached."""


class CassandraServiceUnavailable(Exception):
    """Raied when the Cassandra microservice can't be reached."""


def authenticate(username, password):
    """Ask the auth microservice whether these credentials are valid.

    Returns True / False. Raises AuthServiceUnavailable if the service is down.
    """
    try:
        with grpc.insecure_channel('localhost:50052') as channel:
            stub = auth_pb2_grpc.AuthStub(channel)
            response = stub.Login(
                auth_pb2.LoginRequest(username=username, password=password),
                timeout=5)    # don't let a hung auth service block the request
            return response.ok
    except grpc.RpcError as err:
        raise AuthServiceUnavailable() from err


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
    if not username or not password:
        return jsonify(status='ERROR'), 400     # missing credentials

    try:
        ok = authenticate(username, password)
    except AuthServiceUnavailable:
        return jsonify(status='ERROR'), 503     # auth service unavailable

    if not ok:
        return jsonify(status='ERROR'), 401     # invalid credentials

    # Remember who this browser is, so /app can check it later
    session['username'] = username
    return jsonify(status='SUCCESS', redirect=url_for('message_app')), 200


@app.route('/app')
def message_app():

    # Prevent direct access into '/app' without logging in
    if 'username' not in session:
        return redirect(url_for('index'))
    
    return send_file('message.html')


@app.route('/messages', methods=['POST'])
def handle_incoming_message():
    
    data = request.get_json()
    print(f'Received message, content: \n', data)

    # Send request to handler
    try:
        with grpc.insecure_channel("localhost:50051") as channel:
            stub = cassandra_handler_pb2_grpc.CassandraHandlerStub(channel)
            response = stub.AddMessage(cassandra_handler_pb2.AddMessageRequest(
                senderID=69420,
                receiverID=112233,
                content=data['content']
            ))
            if (response.ok):
                print("Client received message successfully")
            else:
                print(f'error: {response.err}')

            return jsonify(status='SUCCESS'), 200
    except grpc.RpcError:
        return jsonify(status='ERROR'), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
