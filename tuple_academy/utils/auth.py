"""
utils/auth.py — JWT helpers and route decorators
"""

import jwt
import hashlib
import hmac
import os
from functools import wraps
from flask import request, jsonify, current_app
from database import get_db


# ── Password hashing (using hashlib since bcrypt isn't available) ───────────

def hash_password(password: str) -> str:
    """SHA-256 + salt. Use bcrypt in production if available."""
    salt = os.urandom(32).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split('$')
        check = hashlib.sha256((salt + password).encode()).hexdigest()
        return hmac.compare_digest(check, hashed)
    except Exception:
        return False


# ── JWT ─────────────────────────────────────────────────────────────────────

def generate_token(user_id: int, role: str) -> str:
    import time
    payload = {
        'user_id': user_id,
        'role':    role,
        'exp':     int(time.time()) + 60 * 60 * 24 * 7  # 7 days
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_request() -> str | None:
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:]
    return request.args.get('token')


# ── Decorators ───────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (payload['user_id'],)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 401

        request.current_user = dict(user)
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        if payload.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ? AND role = "admin"', (payload['user_id'],)).fetchone()
        if not user:
            return jsonify({'error': 'Access denied'}), 403

        request.current_user = dict(user)
        return f(*args, **kwargs)
    return decorated
