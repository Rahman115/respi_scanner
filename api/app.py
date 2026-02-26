#!/usr/bin/env python3
"""
Absensi API - Complete Modular Version
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
from datetime import datetime #

# Import custom JSON encoder dari utils
from utils.json_encoder import setup_json_provider, CustomJSONEncoder

# Import all blueprints
from blueprints.auth import auth_bp
from blueprints.system import system_bp
from blueprints.students import students_bp
from blueprints.teachers import teachers_bp
from blueprints.classes import classes_bp
from blueprints.attendance import attendance_bp
from blueprints.qrcode import qrcode_bp
from blueprints.scanner import scanner_bp
from blueprints.debug import debug_bp

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

# Setup custom JSON provider
if setup_json_provider(app):
    logger.info("Custom JSON provider berhasil di-setup")
else:
    logger.warning("Gagal setup custom JSON provider, menggunakan default")
    
# Flask app
CORS(app)

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(system_bp)
app.register_blueprint(students_bp)
app.register_blueprint(teachers_bp)
app.register_blueprint(classes_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(qrcode_bp)
app.register_blueprint(scanner_bp)
app.register_blueprint(debug_bp)

# Root endpoint - API Documentation
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "Absensi API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "documentation": {
            "auth": {
                "login": "POST /api/auth/login"
            },
            "students": {
                "get_all": "GET /api/students",
                "get_by_nis": "GET /api/students/<nis>",
                "add": "POST /api/students/add",
                "update": "PUT /api/students/<nis>",
                "delete": "DELETE /api/students/<nis>",
                "by_kelas": "GET /api/students/by-kelas/<kelas_id>",
                "statistics": "GET /api/students/statistics/by-kelas",
                "check_nisn": "GET /api/students/check-nisn"
            },
            "teachers": {
                "get_all": "GET /api/guru",
                "get_by_id": "GET /api/guru/<id>",
                "get_by_nip": "GET /api/guru/nip/<nip>",
                "add": "POST /api/guru",
                "update": "PUT /api/guru/<id>",
                "delete": "DELETE /api/guru/<id>",
                "search": "GET /api/guru/search",
                "with_kelas": "GET /api/guru/with-kelas",
                "statistics": "GET /api/guru/statistics"
            },
            "classes": {
                "get_all": "GET /api/kelas",
                "get_by_id": "GET /api/kelas/<id>",
                "add": "POST /api/kelas",
                "update": "PUT /api/kelas/<id>",
                "delete": "DELETE /api/kelas/<id>",
                "by_jurusan": "GET /api/kelas/by-jurusan/<jurusan_id>",
                "by_tingkat": "GET /api/kelas/by-tingkat/<tingkat>",
                "by_wali_kelas": "GET /api/kelas/wali-kelas/<guru_id>",
                "statistics": "GET /api/kelas/statistics",
                "students": "GET /api/kelas/<id>/siswa"
            },
            "attendance": {
                "today": "GET /api/attendance/today",
                "by_date": "GET /api/attendance/by-date",
                "student": "GET /api/attendance/student/<nis>",
                "statistics": "GET /api/attendance/statistics",
                "summary_by_class": "GET /api/attendance/summary/by-class",
                "manual": "POST /api/attendance/manual",
                "update": "PUT /api/attendance/<id>",
                "delete": "DELETE /api/attendance/<id>"
            },
            "qrcode": {
                "generate": "GET /api/qr/generate/<nis>",
                "bulk_generate": "POST /api/qr/bulk/generate",
                "verify": "POST /api/qr/verify",
                "history": "GET /api/qr/history/<nis>",
                "print": "GET /api/qr/print/<nis>",
                "validate_nisn": "POST /api/qr/validate-nisn"
            },
            "scanner": {
                "scan_nis": "POST /api/scan",
                "scan_nisn": "POST /api/scan-nisn",
                "status": "GET /api/scan-status/<nis>",
                "history": "GET /api/scan-history"
            },
            "system": {
                "health": "GET /api/system/health",
                "test": "GET /api/system/test"
            },
            "debug": {
                "table_structure": "GET /api/debug/table-structure",
                "backup": "POST /api/debug/backup",
                "backups": "GET /api/debug/backups",
                "restore": "POST /api/debug/restore",
                "logs": "GET /api/debug/logs",
                "performance": "GET /api/debug/performance",
                "fix_nisn": "POST /api/debug/fix-nisn",
                "cleanup": "POST /api/debug/cleanup"
            }
        }
    })

# Legacy support - redirect old endpoints
@app.route('/api/test', methods=['GET'])
def test_legacy():
    return jsonify({
        "success": True,
        "message": "Absensi API is running",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "note": "This is a legacy endpoint. Please use / for documentation."
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "Endpoint tidak ditemukan",
        "path": request.path
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "message": "Method tidak diizinkan"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500

def create_directories():
    """Create necessary directories"""
    directories = [
        "/var/www/html/api/logs",
        "/var/www/html/api/qr_codes",
        "/var/www/html/api/backups",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory ensured: {directory}")

if __name__ == "__main__":
    # Create directories
    create_directories()

    # Log startup
    logger.info("=" * 60)
    logger.info("ABSENSI API - COMPLETE MODULAR VERSION")
    logger.info("=" * 60)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Server: {API_CONFIG['host']}:{API_CONFIG['port']}")
    logger.info(f"Debug Mode: {API_CONFIG['debug']}")
    logger.info("=" * 60)
    logger.info("Registered Blueprints:")
    logger.info("  - auth")
    logger.info("  - system")
    logger.info("  - students")
    logger.info("  - teachers")
    logger.info("  - classes")
    logger.info("  - attendance")
    logger.info("  - qrcode")
    logger.info("  - scanner")
    logger.info("  - debug")
    logger.info("=" * 60)

    # Run the application
    app.run(
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        debug=API_CONFIG["debug"],
        threaded=API_CONFIG["threaded"],
    )