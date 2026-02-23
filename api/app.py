#!/usr/bin/env python3
"""
Absensi API - Versi Modular
Migrasi bertahap dari api.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
from datetime import datetime

# Import blueprints yang sudah selesai
from blueprints.auth import auth_bp
from blueprints.system import system_bp
from blueprints.students import students_bp
# Import config
from config import API_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/www/html/api/logs/api.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints yang sudah selesai
app.register_blueprint(auth_bp)
app.register_blueprint(system_bp)
app.register_blueprint(students_bp)

# TODO: Register blueprints berikutnya setelah selesai

# app.register_blueprint(teachers_bp)
# app.register_blueprint(classes_bp)
# app.register_blueprint(attendance_bp)
# app.register_blueprint(qrcode_bp)
# app.register_blueprint(scanner_bp)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "Absensi API",
        "version": "2.0.0",
        "status": "running (migrasi bertahap)",
        "timestamp": datetime.now().isoformat(),
        "endpoints_tersedia": [
            "/api/auth/login",
            "/api/system/health",
            "/api/system/test"
        ],
        "endpoints_menyusul": [
            "/api/students/*",
            "/api/teachers/*", 
            "/api/classes/*",
            "/api/attendance/*",
            "/api/qrcode/*",
            "/api/scanner/*"
        ]
    })

@app.route('/api/test-old', methods=['GET'])
def test_old():
    """Test endpoint (kompatibilitas dengan versi lama)"""
    return jsonify({
        "success": True,
        "message": "Absensi API is running (legacy endpoint)",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "Endpoint tidak ditemukan",
        "path": request.path
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"success": False, "message": "Internal server error"}), 500

def create_directories():
    os.makedirs("/var/www/html/api/logs", exist_ok=True)

if __name__ == "__main__":
    create_directories()
    logger.info("=" * 50)
    logger.info("Starting Absensi API Server (Modular Version)")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    app.run(
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        debug=API_CONFIG["debug"],
        threaded=API_CONFIG["threaded"],
    )
