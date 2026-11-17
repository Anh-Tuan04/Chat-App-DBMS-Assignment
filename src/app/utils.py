from flask import session, jsonify, g
from flask.sessions import SecureCookieSessionInterface
from functools import wraps


class SkippableSessionInterface(SecureCookieSessionInterface):
    def save_session(self, app, session, response):
        if g.get("skip_session_cookie"):
            return  # don't set, refresh, or delete the cookie
        return super().save_session(app, session, response)


def error_response(message, status_code):
    """Return a JSON error tuple and suppress the session cookie."""
    g.skip_session_cookie = True
    return jsonify({"message": message}), status_code


def login_required(f):
    """Returns an error response 401 if not logged in"""
    @wraps(f)
    def wrapper(*arg, **kwargs):
        if "user_id" not in session:
            return error_response("401 Unauthorized", 401)
        return f(*arg, **kwargs)
    return wrapper