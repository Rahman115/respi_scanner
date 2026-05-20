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
        attendance_type = data.get('tipe', 'datang')  # 'datang' atau 'pulang'

        logger.info(f"NISN scan received | NISN={nisn} | IP={request.remote_addr} | Location={location} | Type={attendance_type}")

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
        now = datetime.now()

        logger.info(f"Prosesing absensi untuk {student['nama']} (NISN: {student['nisn']}) dengan tipe {attendance_type}")
        # Handle berdasarkan tipe absensi
        if attendance_type == 'datang':
            logger.info(f"masuk absensi datang untuk {student['nama']} (ID: {student['id']}) (DATE: {today})")
            # Cek apakah sudah datang hari ini
            existing_datang = fetch_one("""
                SELECT a.id, a.waktu, k.nama_kelas FROM absensi a JOIN siswa s ON a.siswa_id = s.id JOIN kelas k ON s.kelas_id = k.id WHERE a.siswa_id = %s AND a.tanggal = %s AND a.status = 'hadir'
            """, (student['id'], today))

            logger.info(f"cek absensi datang untuk {student} -kelas: {existing_datang['nama_kelas']} existing_datang: {existing_datang}")
            if existing_datang:
                return jsonify({
                    "success": False,
                    "message": f"{student['nama']} sudah melakukan check-in hari ini pada pukul {existing_datang['waktu']}",
                    "student": {
                        "nis": student['nis'],
                        "nisn": student['nisn'],
                        "nama": student['nama'],
                        "kelas": existing_datang['nama_kelas']
                    }
                }), 409

            # Save attendance for DATANG (check-in)
            result = execute("""
                INSERT INTO absensi
                (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                student['id'],
                student['nis'],
                today,
                now.time(),
                'hadir',  # status = 'hadir' untuk datang
                'scanner',
                location
            ), commit=True)

            if not result['success']:
                return jsonify({
                    "success": False,
                    "message": "Gagal menyimpan absensi datang"
                }), 500

            message = f"Check-in berhasil untuk {student['nama']}"
            
        elif attendance_type == 'pulang':
            # Cek apakah sudah datang hari ini (harus datang dulu sebelum pulang)
            sudah_datang = fetch_one("""
                SELECT id, waktu FROM absensi 
                WHERE siswa_id = %s AND tanggal = %s AND status = 'hadir'
            """, (student['id'], today))

            logger.info(f"cek absensi pulang untuk {student['nama']} - sudah_datang: {sudah_datang}")

            if not sudah_datang:
                return jsonify({
                    "success": False,
                    "message": f"{student['nama']} belum melakukan check-in hari ini. Silakan check-in terlebih dahulu.",
                    "student": {
                        "nis": student['nis'],
                        "nisn": student['nisn'],
                        "nama": student['nama'],
                        "kelas": student.get('kelas', '-')
                    }
                }), 400

            # Cek apakah sudah pulang hari ini
            existing_pulang = fetch_one("""
                SELECT id FROM absensi 
                WHERE siswa_id = %s AND tanggal = %s AND status = 'pulang'
            """, (student['id'], today))

            if existing_pulang:
                return jsonify({
                    "success": False,
                    "message": f"{student['nama']} sudah melakukan check-out hari ini",
                    "student": {
                        "nis": student['nis'],
                        "nisn": student['nisn'],
                        "nama": student['nama'],
                        "kelas": student.get('kelas', '-')
                    }
                }), 409

            # Save attendance for PULANG (check-out)
            result = execute("""
                INSERT INTO absensi
                (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                student['id'],
                student['nis'],
                today,
                now.time(),
                'pulang',  # status = 'pulang' untuk check-out
                'scanner',
                location
            ), commit=True)

            if not result['success']:
                return jsonify({
                    "success": False,
                    "message": "Gagal menyimpan absensi pulang"
                }), 500

            message = f"Check-out berhasil untuk {student['nama']}"
            
        else:
            return jsonify({
                "success": False,
                "message": f"Tipe absensi tidak valid: {attendance_type}. Gunakan 'datang' atau 'pulang'"
            }), 400

        # Return success response
        return jsonify({
            "success": True,
            "message": message,
            "student": {
                "nis": student['nis'],
                "nisn": student['nisn'],
                "nama": student['nama'],
                "gender": student['gender'],
                "kelas": student.get('kelas', '-')
            },
            "attendance": {
                "id": result.get('last_id'),
                "date": str(today),
                "time": now.strftime("%H:%M:%S"),
                "method": "Scanner",
                "location": location,
                "type": attendance_type
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
