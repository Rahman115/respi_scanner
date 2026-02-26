# blueprints/debug.py
from flask import Blueprint, request, jsonify, send_file
from utils.database import fetch_one, fetch_all, execute, get_db
from utils.auth import token_required
from datetime import datetime
import os
import logging
import json
import subprocess

debug_bp = Blueprint('debug', __name__, url_prefix='/api/debug')
logger = logging.getLogger(__name__)


# ===========================================
# TABLE STRUCTURE CHECK
# ===========================================
@debug_bp.route('/table-structure', methods=['GET'])
@token_required
def table_structure():
    """Check table structure for debugging"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Check siswa table structure
        cursor.execute("DESCRIBE siswa")
        siswa_structure = cursor.fetchall()

        # Check kelas table structure
        cursor.execute("DESCRIBE kelas")
        kelas_structure = cursor.fetchall()

        # Check guru table structure
        cursor.execute("DESCRIBE guru")
        guru_structure = cursor.fetchall()

        # Check absensi table structure
        cursor.execute("DESCRIBE absensi")
        absensi_structure = cursor.fetchall()

        # Sample data from each table
        cursor.execute("SELECT nis, nisn, nama, gender, kelas_id FROM siswa LIMIT 5")
        siswa_sample = cursor.fetchall()

        cursor.execute("SELECT id, nama_kelas, tingkat, jurusan_id, wali_kelas_id FROM kelas LIMIT 5")
        kelas_sample = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "tables": {
                "siswa": {
                    "structure": siswa_structure,
                    "sample": siswa_sample
                },
                "kelas": {
                    "structure": kelas_structure,
                    "sample": kelas_sample
                },
                "guru": {
                    "structure": guru_structure
                },
                "absensi": {
                    "structure": absensi_structure
                }
            }
        })

    except Exception as e:
        logger.error(f"Table structure error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# DATABASE BACKUP
# ===========================================
@debug_bp.route('/backup', methods=['POST'])
@token_required
def create_backup():
    """Create database backup"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "/var/www/html/api/backups"
        backup_file = f"{backup_dir}/backup_{timestamp}.sql"

        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)

        # Get database config
        from config import DB_CONFIG

        # Create backup using mysqldump
        cmd = [
            'mysqldump',
            '-h', DB_CONFIG['host'],
            '-u', DB_CONFIG['user'],
            f'-p{DB_CONFIG["password"]}',
            DB_CONFIG['database']
        ]

        try:
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                return jsonify({
                    "success": False,
                    "message": "Gagal membuat backup"
                }), 500

            file_size = os.path.getsize(backup_file)

            return jsonify({
                "success": True,
                "message": "Backup berhasil dibuat",
                "backup_file": f"backup_{timestamp}.sql",
                "size": file_size,
                "size_formatted": f"{file_size / 1024:.2f} KB",
                "timestamp": timestamp
            })

        except Exception as e:
            logger.error(f"Backup execution error: {e}")
            return jsonify({
                "success": False,
                "message": f"Gagal menjalankan backup: {str(e)}"
            }), 500

    except Exception as e:
        logger.error(f"Backup error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# LIST BACKUPS
# ===========================================
@debug_bp.route('/backups', methods=['GET'])
@token_required
def list_backups():
    """List all available backups"""
    try:
        backup_dir = "/var/www/html/api/backups"
        backups = []

        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                if file.endswith('.sql'):
                    file_path = os.path.join(backup_dir, file)
                    stat = os.stat(file_path)
                    backups.append({
                        "filename": file,
                        "size": stat.st_size,
                        "size_formatted": f"{stat.st_size / 1024:.2f} KB",
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })

        # Sort by modified date descending
        backups.sort(key=lambda x: x['modified'], reverse=True)

        return jsonify({
            "success": True,
            "total": len(backups),
            "backups": backups
        })

    except Exception as e:
        logger.error(f"List backups error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# DOWNLOAD BACKUP
# ===========================================
@debug_bp.route('/backups/<filename>', methods=['GET'])
@token_required
def download_backup(filename):
    """Download a backup file"""
    try:
        backup_dir = "/var/www/html/api/backups"
        file_path = os.path.join(backup_dir, filename)

        # Security: prevent directory traversal
        if '..' in filename or not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "message": "File tidak ditemukan"
            }), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )

    except Exception as e:
        logger.error(f"Download backup error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# RESTORE BACKUP
# ===========================================
@debug_bp.route('/restore', methods=['POST'])
@token_required
def restore_backup():
    """Restore database from backup"""
    try:
        data = request.get_json()

        if not data or 'filename' not in data:
            return jsonify({
                "success": False,
                "message": "Filename diperlukan"
            }), 400

        filename = data['filename']
        backup_dir = "/var/www/html/api/backups"
        file_path = os.path.join(backup_dir, filename)

        if '..' in filename or not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "message": "File backup tidak ditemukan"
            }), 404

        # Get database config
        from config import DB_CONFIG

        # Restore using mysql
        cmd = [
            'mysql',
            '-h', DB_CONFIG['host'],
            '-u', DB_CONFIG['user'],
            f'-p{DB_CONFIG["password"]}',
            DB_CONFIG['database']
        ]

        try:
            with open(file_path, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                return jsonify({
                    "success": False,
                    "message": f"Gagal restore: {result.stderr}"
                }), 500

            return jsonify({
                "success": True,
                "message": f"Database berhasil direstore dari {filename}"
            })

        except Exception as e:
            logger.error(f"Restore execution error: {e}")
            return jsonify({
                "success": False,
                "message": f"Gagal menjalankan restore: {str(e)}"
            }), 500

    except Exception as e:
        logger.error(f"Restore error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# SYSTEM LOGS
# ===========================================
@debug_bp.route('/logs', methods=['GET'])
@token_required
def get_logs():
    """Get application logs"""
    try:
        lines = request.args.get('lines', 100, type=int)
        log_file = "/var/www/html/api/logs/api.log"

        if not os.path.exists(log_file):
            return jsonify({
                "success": False,
                "message": "Log file tidak ditemukan"
            }), 404

        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return jsonify({
            "success": True,
            "total_lines": len(all_lines),
            "displayed_lines": len(last_lines),
            "logs": last_lines
        })

    except Exception as e:
        logger.error(f"Get logs error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# DATABASE PERFORMANCE
# ===========================================
@debug_bp.route('/performance', methods=['GET'])
@token_required
def check_performance():
    """Check database performance"""
    try:
        from config import DB_CONFIG
        
        conn = get_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Get table sizes
        cursor.execute("""
            SELECT
                table_name,
                ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                table_rows as row_count
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            ORDER BY size_mb DESC
        """)
        table_sizes = cursor.fetchall()

        # Get database stats
        cursor.execute("SHOW STATUS LIKE 'Questions'")
        questions = cursor.fetchone()

        cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
        slow_queries = cursor.fetchone()

        cursor.execute("SHOW VARIABLES LIKE 'long_query_time'")
        long_query_time = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "database": {
                "name": DB_CONFIG['database'],
                "host": DB_CONFIG['host']
            },
            "table_sizes": table_sizes,
            "performance_stats": {
                "questions": questions['Value'] if questions else 'N/A',
                "slow_queries": slow_queries['Value'] if slow_queries else 'N/A',
                "long_query_time": long_query_time['Value'] if long_query_time else 'N/A'
            }
        })

    except Exception as e:
        logger.error(f"Performance check error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# FIX NISN (Utility)
# ===========================================
@debug_bp.route('/fix-nisn', methods=['POST'])
@token_required
def fix_nisn():
    """Fix NISN format (remove spaces, ensure 10 digits)"""
    try:
        # Get all students with invalid NISN
        students = fetch_all("""
            SELECT id, nis, nisn, nama
            FROM siswa
            WHERE LENGTH(TRIM(nisn)) != 10 OR TRIM(nisn) NOT REGEXP '^[0-9]+$'
        """)

        fixed_count = 0
        fixes = []

        for student in students:
            original_nisn = student['nisn']
            if original_nisn:
                # Remove non-digits
                import re
                cleaned = re.sub(r'\D', '', str(original_nisn))

                # Take last 10 digits if longer
                if len(cleaned) > 10:
                    cleaned = cleaned[-10:]

                if len(cleaned) == 10 and cleaned != original_nisn:
                    # Update
                    result = execute(
                        "UPDATE siswa SET nisn = %s WHERE id = %s",
                        (cleaned, student['id']),
                        commit=True
                    )
                    if result['success']:
                        fixed_count += 1
                        fixes.append({
                            "nis": student['nis'],
                            "nama": student['nama'],
                            "old_nisn": original_nisn,
                            "new_nisn": cleaned
                        })

        return jsonify({
            "success": True,
            "message": f"Berhasil memperbaiki {fixed_count} NISN",
            "total_checked": len(students),
            "fixed": fixed_count,
            "details": fixes
        })

    except Exception as e:
        logger.error(f"Fix NISN error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# DATABASE CLEANUP
# ===========================================
@debug_bp.route('/cleanup', methods=['POST'])
@token_required
def cleanup_database():
    """Clean up orphaned records"""
    try:
        results = {}

        # Remove absensi without valid siswa
        result = execute("""
            DELETE a FROM absensi a
            LEFT JOIN siswa s ON a.siswa_id = s.id
            WHERE s.id IS NULL
        """, commit=True)
        results['orphaned_attendance'] = result.get('rowcount', 0)

        # Remove siswa with invalid kelas_id
        result = execute("""
            DELETE s FROM siswa s
            LEFT JOIN kelas k ON s.kelas_id = k.id
            WHERE k.id IS NULL AND s.kelas_id IS NOT NULL
        """, commit=True)
        results['invalid_kelas_siswa'] = result.get('rowcount', 0)

        return jsonify({
            "success": True,
            "message": "Database cleanup completed",
            "deleted": results
        })

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
