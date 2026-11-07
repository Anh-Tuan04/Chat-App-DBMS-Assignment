from flask import Flask, jsonify, redirect, request, session, url_for, send_from_directory
import functools
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = PROJECT_ROOT / 'templates'
STATIC_DIR = PROJECT_ROOT / 'static'


app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    static_url_path='/static'    
)


app.secret_key = 'dev' # change to a config later


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
    return send_from_directory(TEMPLATE_DIR, 'login.html')