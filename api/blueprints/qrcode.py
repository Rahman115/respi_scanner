# blueprints/qrcode.py
from flask import Blueprint, request, jsonify
from utils.database import fetch_one, fetch_all, execute
from utils.auth import token_required
from utils.helpers import generate_qr_image, validate_nisn
from datetime import date, datetime
import logging

qrcode_bp = Blueprint('qrcode', __name__, url_prefix='/api/qr')
logger = logging.getLogger(__name__)


# ===========================================
# GENERATE QR CODE FOR SINGLE STUDENT
# ===========================================
@qrcode_bp.route('/generate/<nis>', methods=['GET'])
@token_required
def generate_qr_code(nis):
    """Generate QR code for a single student"""
    try:
        # Get student data
        student = fetch_one("""
            SELECT id, nis, nisn, nama, gender, kelas_id, card_version
            FROM siswa 
            WHERE nis = %s
        """, (nis,))

        if not student:
            return jsonify({
                "success": False,
                "message": f"Siswa dengan NIS {nis} tidak ditemukan"
            }), 404

        # Validate NISN
        nisn_value = str(student['nisn']).strip()
        if not validate_nisn(nisn_value):
            return jsonify({
                "success": False,
                "message": f"NISN harus 10 digit angka. Saat ini: {nisn_value} ({(len(nisn_value))} digit)"
            }), 400

        # Generate QR code (hanya berisi NISN)
        qr_data = nisn_value
        qr_base64 = generate_qr_image(qr_data)

        if not qr_base64:
            return jsonify({
                "success": False,
                "message": "Gagal menghasilkan QR code"
            }), 500

        # Get kelas info
        kelas = fetch_one("""
            SELECT k.nama_kelas, k.tingkat, j.nama as jurusan
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            WHERE k.id = %s
        """, (student['kelas_id'],))

        return jsonify({
            "success": True,
            "student": {
                "nis": student['nis'],
                "nisn": student['nisn'],
                "nama": student['nama'],
                "gender": student['gender'],
                "gender_label": "Laki-laki" if student['gender'] == 'L' else "Perempuan",
                "kelas": kelas['nama_kelas'] if kelas else '-',
                "tingkat": kelas['tingkat'] if kelas else '-',
                "jurusan": kelas['jurusan'] if kelas else '-',
                "kelas_id": student['kelas_id'],
                "card_version": student['card_version']
            },
            "qr_data": qr_data,
            "qr_image": f"data:image/png;base64,{qr_base64}"
        })

    except Exception as e:
        logger.error(f"QR generation error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# BULK GENERATE QR CODES
# ===========================================
@qrcode_bp.route('/bulk/generate', methods=['POST'])
@token_required
def generate_bulk_qr():
    """Generate QR codes for multiple students"""
    try:
        data = request.get_json()

        if not data or 'nis_list' not in data:
            return jsonify({
                "success": False,
                "message": "List NIS diperlukan"
            }), 400

        nis_list = data['nis_list']
        if not isinstance(nis_list, list):
            return jsonify({
                "success": False,
                "message": "nis_list harus berupa array"
            }), 400

        if len(nis_list) > 50:
            return jsonify({
                "success": False,
                "message": "Maksimal 50 siswa per batch"
            }), 400

        qr_results = []
        success_count = 0
        error_count = 0

        for nis in nis_list:
            # Get student data
            student = fetch_one("""
                SELECT id, nis, nisn, nama, gender, kelas_id
                FROM siswa 
                WHERE nis = %s
            """, (nis,))

            if not student:
                qr_results.append({
                    "nis": nis,
                    "error": "Siswa tidak ditemukan",
                    "qr_data": None,
                    "qr_image": None
                })
                error_count += 1
                continue

            # Validate NISN
            nisn_value = str(student['nisn']).strip()
            if not validate_nisn(nisn_value):
                qr_results.append({
                    "nis": student['nis'],
                    "nama": student['nama'],
                    "error": f"NISN tidak valid: {nisn_value}",
                    "qr_data": None,
                    "qr_image": None
                })
                error_count += 1
                continue

            # Generate QR code
            qr_data = nisn_value
            qr_base64 = generate_qr_image(qr_data)

            if qr_base64:
                qr_results.append({
                    "nis": student['nis'],
                    "nisn": student['nisn'],
                    "nama": student['nama'],
                    "gender": student['gender'],
                    "qr_data": qr_data,
                    "qr_image": f"data:image/png;base64,{qr_base64}"
                })
                success_count += 1
            else:
                qr_results.append({
                    "nis": student['nis'],
                    "nama": student['nama'],
                    "error": "Gagal generate QR",
                    "qr_data": None,
                    "qr_image": None
                })
                error_count += 1

        return jsonify({
            "success": True,
            "count": len(qr_results),
            "success_count": success_count,
            "error_count": error_count,
            "qr_codes": qr_results
        })

    except Exception as e:
        logger.error(f"Bulk QR generation error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# VERIFY QR CODE SCAN
# ===========================================
@qrcode_bp.route('/verify', methods=['POST'])
def verify_qr_code():
    """Verify and process QR code scan (public endpoint, no token needed)"""
    try:
        data = request.get_json()

        if not data or 'qr_data' not in data:
            return jsonify({
                "success": False,
                "message": "QR data diperlukan"
            }), 400

        qr_data = data['qr_data'].strip()
        location = data.get('location', 'QR Scanner')

        logger.info(f"QR scan received | NISN={qr_data} | IP={request.remote_addr}")

        # Validate NISN format
        if not validate_nisn(qr_data):
            logger.warning(f"Invalid NISN format: {qr_data}")
            return jsonify({
                "success": False,
                "message": "Format NISN tidak valid. Harus 10 digit angka"
            }), 400

        # Find student by NISN
        student = fetch_one("""
            SELECT id, nis, nisn, nama, gender, kelas_id
            FROM siswa 
            WHERE nisn = %s
        """, (qr_data,))

        if not student:
            logger.warning(f"QR scan with unknown NISN: {qr_data}")
            return jsonify({
                "success": False,
                "message": "Siswa tidak valid"
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
            'QR Scanner',
            location
        ), commit=True)

        if not result['success']:
            return jsonify({
                "success": False,
                "message": "Gagal menyimpan absensi"
            }), 500

        return jsonify({
            "success": True,
            "message": "Absensi QR berhasil",
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
                "method": "QR Scanner",
                "location": location
            }
        })

    except Exception as e:
        logger.error(f"QR verification error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET STUDENT QR HISTORY
# ===========================================
@qrcode_bp.route('/history/<nis>', methods=['GET'])
@token_required
def get_qr_history(nis):
    """Get QR code generation history for a student"""
    try:
        # Check if student exists
        student = fetch_one("SELECT id, nama FROM siswa WHERE nis = %s", (nis,))
        if not student:
            return jsonify({
                "success": False,
                "message": f"Siswa dengan NIS {nis} tidak ditemukan"
            }), 404

        # Get QR generation history (from logs or a separate table)
        # For now, return the current QR code
        current_qr = fetch_one("""
            SELECT nisn, card_version 
            FROM siswa 
            WHERE nis = %s
        """, (nis,))

        return jsonify({
            "success": True,
            "student": {
                "nis": nis,
                "nama": student['nama']
            },
            "current_qr": {
                "data": current_qr['nisn'],
                "card_version": current_qr['card_version'],
                "generated_at": datetime.now().isoformat()
            },
            "history": []  # Can be expanded later
        })

    except Exception as e:
        logger.error(f"Get QR history error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# PRINT QR CODE (returns printable version)
# ===========================================
@qrcode_bp.route('/print/<nis>', methods=['GET'])
@token_required
def print_qr_code(nis):
    """Get QR code in printable format (with student info)"""
    try:
        # Get student data with kelas info
        student = fetch_one("""
            SELECT 
                s.id, s.nis, s.nisn, s.nama, s.gender,
                s.kelas_id, s.card_version,
                k.nama_kelas as kelas,
                k.tingkat,
                j.nama as jurusan
            FROM siswa s
            LEFT JOIN kelas k ON s.kelas_id = k.id
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            WHERE s.nis = %s
        """, (nis,))

        if not student:
            return jsonify({
                "success": False,
                "message": f"Siswa dengan NIS {nis} tidak ditemukan"
            }), 404

        # Validate NISN
        nisn_value = str(student['nisn']).strip()
        if not validate_nisn(nisn_value):
            return jsonify({
                "success": False,
                "message": "NISN tidak valid untuk dicetak"
            }), 400

        # Generate QR code
        qr_base64 = generate_qr_image(nisn_value)

        if not qr_base64:
            return jsonify({
                "success": False,
                "message": "Gagal generate QR"
            }), 500

        return jsonify({
            "success": True,
            "print_data": {
                "qr_image": f"data:image/png;base64,{qr_base64}",
                "student_info": {
                    "nama": student['nama'],
                    "nis": student['nis'],
                    "nisn": student['nisn'],
                    "kelas": f"{student['tingkat']} {student['jurusan']} {student['kelas']}".strip(),
                    "gender": "Laki-laki" if student['gender'] == 'L' else "Perempuan"
                },
                "print_config": {
                    "paper_size": "A4",
                    "qr_size": "5cm",
                    "copies": 1
                }
            }
        })

    except Exception as e:
        logger.error(f"Print QR error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# VALIDATE NISN (utility endpoint)
# ===========================================
@qrcode_bp.route('/validate-nisn', methods=['POST'])
@token_required
def validate_nisn_endpoint():
    """Validate NISN format and existence"""
    try:
        data = request.get_json()

        if not data or 'nisn' not in data:
            return jsonify({
                "success": False,
                "message": "NISN diperlukan"
            }), 400

        nisn = data['nisn'].strip()

        # Check format
        is_valid_format = validate_nisn(nisn)

        # Check if exists in database
        student = None
        if is_valid_format:
            student = fetch_one("""
                SELECT nis, nisn, nama, gender, kelas_id
                FROM siswa 
                WHERE nisn = %s
            """, (nisn,))

        return jsonify({
            "success": True,
            "nisn": nisn,
            "is_valid_format": is_valid_format,
            "exists_in_db": student is not None,
            "student": student
        })

    except Exception as e:
        logger.error(f"Validate NISN error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
