# blueprints/system.py
from flask import Blueprint, jsonify
from datetime import datetime
from utils.database import get_db
import logging

system_bp = Blueprint('system', __name__, url_prefix='/api/system')
logger = logging.getLogger(__name__)

@system_bp.route('/health', methods=['GET'])
def health_check():
    db = get_db()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db else "disconnected",
        "version": "2.0.0"
    })

@system_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        "success": True,
        "message": "API berjalan normal",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    })
