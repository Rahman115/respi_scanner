# utils/auth.py
import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
import hashlib
from config import JWT_SECRET_KEY

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"success": False, "message": "Token diperlukan"}), 401
        try:
            if token.startswith("Bearer "):
                token = token[7:]
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "message": "Token tidak valid"}), 401
        return f(*args, **kwargs)
    return decorated

def create_token(user):
    return jwt.encode({
        "user_id": user["id"],
        "username": user["username"],
        "nama": user["nama"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=24)
    }, JWT_SECRET_KEY, algorithm="HS256")

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
