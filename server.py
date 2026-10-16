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


class MySQLServiceUnavailable(Exception):
    """Raised when the MySQL microservice can't be reached."""


class CassandraServiceUnavailable(Exception):
    """Raied when the Cassandra microservice can't be reached."""


# gRPC channels (and the stubs built on them) are thread-safe and meant to be
# shared, so they are created once here instead of once per request. Channels
# connect lazily, so the handlers don't need to be up when this file is loaded.
mysql_channel = grpc.insecure_channel('localhost:50052')
mysql_stub = mysql_handler_pb2_grpc.MySQLHandlerStub(mysql_channel)

cassandra_channel = grpc.insecure_channel('localhost:50051')
cassandra_stub = cassandra_handler_pb2_grpc.CassandraHandlerStub(cassandra_channel)


def authenticate(username, password):
    """Ask the MySQL handler whether these credentials are valid.

    Returns True / False. Raises MySQLServiceUnavailable if the service is down.
    """
    try:
        response = mysql_stub.Login(
            mysql_handler_pb2.LoginRequest(username=username, password=password),
            timeout=5)    # don't let a hung MySQL handler block the request
        return response.ok
    except grpc.RpcError as err:
        raise MySQLServiceUnavailable() from err


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
    except MySQLServiceUnavailable:
        return jsonify(status='ERROR'), 503     # MySQL handler unavailable

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
        response = cassandra_stub.AddMessage(cassandra_handler_pb2.AddMessageRequest(
            senderID=69420,
            receiverID=112233,
            content=data['content']
        ))
        if (response.ok):
            print("Client received message successfully")
            return jsonify(status='SUCCESS'), 200

        # The handler was reached but failed to store the message
        print(f'error: {response.err}')
        return jsonify(status='ERROR'), 500
    except grpc.RpcError:
        return jsonify(status='ERROR'), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)