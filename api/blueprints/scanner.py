# blueprints/scanner.py
from flask import Blueprint, request, jsonify
from utils.database import fetch_one, fetch_all, execute
from utils.auth import token_required
from utils.helpers import validate_nisn
from datetime import date, datetime
import logging

scanner_bp = Blueprint('scanner', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


# ===========================================
# SCAN NIS (Legacy - Barcode Scanner)
# ===========================================
@scanner_bp.route('/scan', methods=['POST'])
def process_scan():
    """Process barcode scan (legacy - using NIS)"""
    try:
        data = request.get_json()

        if not data or 'nis' not in data:
            return jsonify({
                "success": False,
                "message": "NIS diperlukan"
            }), 400

        nis = str(data['nis']).strip()
        location = data.get('location', 'Scanner USB')

        logger.info(f"Legacy scan received | NIS={nis} | IP={request.remote_addr}")

        # Find student by NIS
        student = fetch_one("""
            SELECT id, nis, nisn, nama, gender, kelas_id
            FROM siswa 
            WHERE nis = %s
        """, (nis,))

        if not student:
            logger.warning(f"Legacy scan with unknown NIS: {nis}")
            return jsonify({
                "success": False,
                "message": f"Siswa dengan NIS {nis} tidak ditemukan"
            }), 404

        # Check if already attended today
        today = date.today()
        existing = fetch_one("""
            SELECT id FROM absensi 
            WHERE siswa_id = %s AND tanggal = %s
        """, (student['id'], today))

        if existing:
            return jsonify({
                "success": False,
                "message": f"{student['nama']} sudah absen hari ini",
                "student": {
                    "nis": student['nis'],
                    "nama": student['nama'],
                    "kelas_id": student['kelas_id']
                }
            }), 409

        # Save attendance
        now = datetime.now()
        result = execute("""
            INSERT INTO absensi
            (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            student['id'],
            student['nis'],
            today,
            now.time(),
            'Hadir',
            'Scanner (Legacy)',
            location
        ), commit=True)

        if not result['success']:
            return jsonify({
                "success": False,
                "message": "Gagal menyimpan absensi"
            }), 500

        # Get kelas info
        kelas = fetch_one("""
            SELECT nama_kelas FROM kelas WHERE id = %s
        """, (student['kelas_id'],))

        return jsonify({
            "success": True,
            "message": "Absensi berhasil",
            "student": {
                "nis": student['nis'],
                "nama": student['nama'],
                "kelas": kelas['nama_kelas'] if kelas else '-'
            },
            "attendance": {
                "date": str(today),
                "time": now.strftime("%H:%M:%S"),
                "method": "Scanner (Legacy)"
            }
        })

    except Exception as e:
        logger.error(f"Legacy scan processing error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# SCAN NISN (New - Barcode Scanner)
# ===========================================
@scanner_bp.route('/scan-nisn', methods=['POST'])
def process_scan_nisn():
    """Process barcode scan using NISN"""
    try:
        data = request.get_json()

        if not data or 'nisn' not in data:
            return jsonify({
                "success": False,
                "message": "NISN diperlukan"
            }), 400

        nisn = str(data['nisn']).strip()
        location = data.get('location', 'Scanner NISN USB')

        logger.info(f"NISN scan received | NISN={nisn} | IP={request.remote_addr}")

        # Validate NISN format
        if not validate_nisn(nisn):
            logger.warning(f"Invalid NISN format: {nisn}")
            return jsonify({
                "success": False,
                "message": f"NISN harus 10 digit angka. Diterima: {nisn}"
            }), 400

        # Find student by NISN
        student = fetch_one("""
            SELECT id, nis, nisn, nama, gender, kelas_id
            FROM siswa 
            WHERE nisn = %s
        """, (nisn,))

        if not student:
            logger.warning(f"NISN scan with unknown NISN: {nisn}")
            return jsonify({
                "success": False,
                "message": f"Siswa dengan NISN {nisn} tidak ditemukan"
            }), 404

        # Check if already attended today
        today = date.today()
        existing = fetch_one("""
            SELECT id FROM absensi 
            WHERE siswa_id = %s AND tanggal = %s
        """, (student['id'], today))

        if existing:
            return jsonify({
                "success": False,
                "message": f"{student['nama']} sudah absen hari ini",
                "student": {
                    "nis": student['nis'],
                    "nisn": student['nisn'],
                    "nama": student['nama']
                }
            }), 409

        # Save attendance
        now = datetime.now()
        result = execute("""
            INSERT INTO absensi
            (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            student['id'],
            student['nis'],
            today,
            now.time(),
            'Hadir',
            'scanner',
            location
        ), commit=True)

        if not result['success']:
            return jsonify({
                "success": False,
                "message": "Gagal menyimpan absensi"
            }), 500

        return jsonify({
            "success": True,
            "message": "Absensi NISN berhasil",
            "student": {
                "nis": student['nis'],
                "nisn": student['nisn'],
                "nama": student['nama'],
                "gender": student['gender']
            },
            "attendance": {
                "id": result.get('last_id'),
                "date": str(today),
                "time": now.strftime("%H:%M:%S"),
                "method": "Scanner"
            }
        })

    except Exception as e:
        logger.error(f"NISN scan processing error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# SCAN STATUS (Check if student can scan)
# ===========================================
@scanner_bp.route('/scan-status/<nis>', methods=['GET'])
def check_scan_status(nis):
    """Check if student can scan today"""
    try:
        # Find student
        student = fetch_one("""
            SELECT id, nis, nisn, nama, kelas_id
            FROM siswa 
            WHERE nis = %s
        """, (nis,))

        if not student:
            return jsonify({
                "success": False,
                "message": f"Siswa dengan NIS {nis} tidak ditemukan"
            }), 404

        # Check today's attendance
        today = date.today()
        existing = fetch_one("""
            SELECT id, waktu FROM absensi 
            WHERE siswa_id = %s AND tanggal = %s
        """, (student['id'], today))

        if existing:
            return jsonify({
                "success": False,
                "message": "Sudah absen hari ini",
                "can_scan": False,
                "attendance": {
                    "time": str(existing['waktu'])
                }
            })

        return jsonify({
            "success": True,
            "message": "Siap scan",
            "can_scan": True,
            "student": {
                "nis": student['nis'],
                "nama": student['nama']
            }
        })

    except Exception as e:
        logger.error(f"Check scan status error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# SCAN HISTORY (Today's scans)
# ===========================================
@scanner_bp.route('/scan-history', methods=['GET'])
@token_required
def get_scan_history():
    """Get today's scan history"""
    try:
        today = date.today()
        limit = request.args.get('limit', 50, type=int)

        scans = fetch_all("""
            SELECT 
                a.waktu,
                a.metode,
                a.scanner_lokasi,
                s.nis,
                s.nama,
                s.gender,
                k.nama_kelas as kelas
            FROM absensi a
            JOIN siswa s ON a.siswa_id = s.id
            LEFT JOIN kelas k ON s.kelas_id = k.id
            WHERE a.tanggal = %s AND a.metode LIKE '%scanner%'
            ORDER BY a.waktu DESC
            LIMIT %s
        """, (today, limit))

        return jsonify({
            "success": True,
            "date": str(today),
            "total": len(scans),
            "scans": scans
        })

    except Exception as e:
        logger.error(f"Get scan history error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
