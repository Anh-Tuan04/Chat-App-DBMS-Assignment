import os
from concurrent import futures

import bcrypt
import grpc
import pymysql

import auth_pb2
import auth_pb2_grpc

# MySQL connection settings. Override with environment variables, e.g. in PowerShell:
#   $env:MYSQL_PASSWORD = "your-password"
DB_CONFIG = dict(
    host=os.environ.get('MYSQL_HOST', 'localhost'),
    port=int(os.environ.get('MYSQL_PORT', '3306')),
    user=os.environ.get('MYSQL_USER', 'root'),
    password=os.environ.get('MYSQL_PASSWORD', ''),
    database=os.environ.get('MYSQL_DB', 'chatapp'),
    charset='utf8mb4',
    connect_timeout=5,
)

# Checked against when the username doesn't exist, so an unknown user takes about
# as long to reject as a wrong password (doesn't reveal which usernames exist).
_DUMMY_HASH = bcrypt.hashpw(b'dummy', bcrypt.gensalt())


class AuthService(auth_pb2_grpc.AuthServicer):
    def Login(self, request, context):
        # 1) Look up the stored hash
        try:
            conn = pymysql.connect(**DB_CONFIG)
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        'SELECT password_hash FROM users WHERE username = %s',
                        (request.username,))
                    row = cursor.fetchone()
            finally:
                conn.close()
        except pymysql.MySQLError as err:
            # A DB problem is not "wrong password": tell the caller we're unavailable
            print(f'Database error: {err}')
            context.abort(grpc.StatusCode.UNAVAILABLE, 'database unavailable')

        # 2) Compare the password with the bcrypt hash
        stored = row[0].encode('utf-8') if row else _DUMMY_HASH
        try:
            matched = bcrypt.checkpw(request.password.encode('utf-8'), stored)
        except ValueError:
            # Stored value isn't a valid bcrypt hash (or password is over bcrypt's limit)
            matched = False

        ok = row is not None and matched
        print(f'Login {"OK" if ok else "FAILED"} for user {request.username!r}')
        return auth_pb2.LoginResponse(ok=ok)


def serve():
    port = '50052'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServicer_to_server(AuthService(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print('Auth service started, listening on ' + port)
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
