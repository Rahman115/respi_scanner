# blueprints/auth.py
from flask import Blueprint, request, jsonify
from utils.database import fetch_one
from utils.auth import hash_password, create_token
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"success": False, "message": "Username/password diperlukan"}), 400

        user = fetch_one(
            "SELECT id, username, nama, role FROM users WHERE username = %s AND password = %s",
            (data['username'], hash_password(data['password']))
        )

        if not user:
            return jsonify({"success": False, "message": "Username/password salah"}), 401

        token = create_token(user)
        return jsonify({
            "success": True,
            "message": "Login berhasil",
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "nama": user["nama"],
                "role": user["role"]
            }
        })
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
