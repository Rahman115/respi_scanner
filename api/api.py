#!/usr/bin/env python3
"""
Absensi API Complete with QR Code Features
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import mysql.connector
from datetime import datetime, date, timedelta
import hashlib
import hmac
import json
import qrcode
import io
import base64
import jwt
from functools import wraps
import os
import logging
from config import QR_SECRET_KEY, JWT_SECRET_KEY, DB_CONFIG, QR_CONFIG, API_CONFIG

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

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# JWT Configuration
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY


def connect_db():
    """Connect to MySQL database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None


def token_required(f):
    """Decorator for JWT token authentication"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"success": False, "message": "Token is missing"}), 401

        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "message": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated


def generate_qr_signature(data):
    """Generate HMAC signature for QR code data"""
    message = json.dumps(data, sort_keys=True).encode()
    signature = hmac.new(QR_SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()
    return signature


def verify_qr_signature(data, signature):
    """Verify QR code signature"""
    expected_signature = generate_qr_signature(data)
    return hmac.compare_digest(expected_signature, signature)


# ===========================================
# AUTHENTICATION ENDPOINTS
# ===========================================


@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login endpoint for admin/teachers"""
    try:
        data = request.get_json()

        if not data or "username" not in data or "password" not in data:
            return (
                jsonify(
                    {"success": False, "message": "Username dan password diperlukan"}
                ),
                400,
            )

        username = data["username"]
        password = data["password"]

        # Hash password (MD5 for compatibility with PHP)
        import hashlib

        hashed_password = hashlib.md5(password.encode()).hexdigest()

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, nama, role FROM users WHERE username = %s AND password = %s",
            (username, hashed_password),
        )

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # Generate JWT token
            token = jwt.encode(
                {
                    "user_id": user["id"],
                    "username": user["username"],
                    "nama": user["nama"],
                    "role": user["role"],
                    "exp": datetime.utcnow() + timedelta(hours=24),
                },
                JWT_SECRET_KEY,
                algorithm="HS256",
            )

            return jsonify(
                {
                    "success": True,
                    "message": "Login berhasil",
                    "token": token,
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "nama": user["nama"],
                        "role": user["role"],
                    },
                }
            )
        else:
            return (
                jsonify({"success": False, "message": "Username atau password salah"}),
                401,
            )

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# QR CODE ENDPOINTS
# ===========================================


@app.route("/api/qr/generate/<nis>", methods=["GET"])
@token_required
def generate_qr_code(nis):
    """Generate QR code for student"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nis,nisn, nama, kelas, card_version FROM siswa WHERE nis = %s",
            (nis,),
        )
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        if not student:
            return jsonify({"success": False, "message": "Siswa tidak ditemukan"}), 404

        # QR data hanya berisi NISN
        nisn_value = str(student["nisn"]).strip()

        # validasi NISN 10 Digit
        if len(nisn_value) != 10:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"NISN harus 10 digit, saat ini {len(nisn_value)} digit: {nisn_value}",
                    }
                ),
                400,
            )

        # hanya NISN saja yang disimpan di dalam QR
        qr_data = nisn_value  # String murni, bukan JSON

        # Convert to string
        # qr_string = json.dumps(qr_data)

        # Generate QR code
        qr = qrcode.QRCode(
            version=QR_CONFIG["version"],
            error_correction=getattr(
                qrcode.constants, f"ERROR_CORRECT_{QR_CONFIG['error_correction']}"
            ),
            box_size=QR_CONFIG["box_size"],
            border=QR_CONFIG["border"],
        )

        qr.add_data(qr_data)  # Hanya NISN
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Convert to base64
        qr_base64 = base64.b64encode(img_bytes.getvalue()).decode("utf-8")

        return jsonify(
            {
                "success": True,
                "student": {
                    "nis": student["nis"],
                    "nisn": student["nisn"],
                    "nama": student["nama"],
                    "kelas": student["kelas"],
                },
                "qr_data": qr_data,
                "qr_image": f"data:image/png;base64,{qr_base64}",
            }
        )

    except Exception as e:
        logger.error(f"QR generation error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/qr/verify", methods=["POST"])
def verify_qr_code():
    """Verify and process QR code scan"""
    try:
        data = request.get_json()

        if not data or "qr_data" not in data:
            return jsonify({"success": False, "message": "QR data diperlukan"}), 400

        qr_data = data["qr_data"]

        logger.info(
            f"NISN QR data received | NISN={qr_data} | IP={request.remote_addr}"
        )

        # Validasi bahwa qr_data adalah string
        if not isinstance(qr_data, str) or len(qr_data) != 10 or not qr_data.isdigit():
            logger.warning(f"Invalid NISN format: {qr_data}")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Format NISN tidak valid. Harus 10 digit angka",
                    }
                ),
                400,
            )

        # Cek apakah nis ada dalam qr_data
        nisn_value = qr_data.strip()

        # Database check
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, nis, nisn, nama, kelas, card_version FROM siswa WHERE nisn = %s",
            (nisn_value,),
        )
        student = cursor.fetchone()

        if not student:
            logger.warning(
                f"QR scan with unknown NISN | NIS={nisn_value} | IP={request.remote_addr}"
            )
            return jsonify({"success": False, "message": "Siswa tidak valid"}), 404

        # nis = nis_value
        location = data.get("location", "QR Scanner")

        # Check if already attended today
        today = date.today()
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (student["id"], today),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f'{student["nama"]} sudah absen hari ini',
                        "student": {
                            "nis": student["nis"],
                            "nama": student["nama"],
                            "kelas": student["kelas"],
                        },
                    }
                ),
                409,
            )

        # Save attendance
        now = datetime.now()
        cursor.execute(
            """INSERT INTO absensi
               (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                student["id"],
                student["nis"],
                today,
                now.time(),
                "Hadir",
                "scanner",
                location,
            ),
        )

        conn.commit()

        # Get the inserted record
        cursor.execute("SELECT LAST_INSERT_ID() as id")
        attendance_id = cursor.fetchone()["id"]

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Absensi QR berhasil",
                "student": {
                    "nis": student["nis"],
                    "nisn": student["nisn"],
                    "nama": student["nama"],
                    "kelas": student["kelas"],
                },
                "attendance": {
                    "id": attendance_id,
                    "date": str(today),
                    "time": now.strftime("%H:%M:%S"),
                    "method": "Scanner",
                    "location": location,
                },
            }
        )

    except Exception as e:
        logger.error(f"QR verification error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/qr/bulk/generate", methods=["POST"])
@token_required
def generate_bulk_qr():
    """Generate QR codes for multiple students"""
    try:
        data = request.get_json()

        if not data or "nis_list" not in data:
            return jsonify({"success": False, "message": "List NIS diperlukan"}), 400

        nis_list = data["nis_list"]

        if not isinstance(nis_list, list):
            return (
                jsonify({"success": False, "message": "nis_list harus berupa array"}),
                400,
            )

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        qr_results = []

        for nis in nis_list:
            cursor.execute(
                "SELECT id, nis,nisn, nama, kelas FROM siswa WHERE nis = %s", (nis,)
            )
            student = cursor.fetchone()

            if student and student.get("nisn"):
                # Generate QR data
                # qr_data = {
                #  'type': 'student_card',
                #  'nis': student['nis'],
                # 'nama': student['nama'],
                # 'kelas': student['kelas'],
                # 'student_id': student['id'],
                #'card_version': student['card_version']
                # 'timestamp': datetime.utcnow().isoformat(),
                # 'expires': (datetime.utcnow() + timedelta(days=30)).isoformat()
                # }

                # signature = generate_qr_signature(qr_data)
                nisn_value = str(
                    student["nisn"]
                ).strip()  # qr_data['signature'] = signature
                # Validasi NISN
                if len(nisn_value) == 10 and nisn_value.isdigit():
                    qr_data = nisn_value

                    # Generate QR code
                    qr = qrcode.QRCode(
                        version=QR_CONFIG["version"],
                        error_correction=getattr(
                            qrcode.constants,
                            f"ERROR_CORRECT_{QR_CONFIG['error_correction']}",
                        ),
                        box_size=QR_CONFIG["box_size"],
                        border=QR_CONFIG["border"],
                    )

                    qr.add_data(qr_data)
                    qr.make(fit=True)

                    img = qr.make_image(fill_color="black", back_color="white")
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    img_bytes.seek(0)

                    qr_base64 = base64.b64encode(img_bytes.getvalue()).decode("utf-8")

                    qr_results.append(
                        {
                            "nis": student["nis"],
                            "nisn": student["nisn"],
                            "nama": student["nama"],
                            "kelas": student["kelas"],
                            "qr_data": qr_data,
                            "qr_image": f"data:image/png;base64,{qr_base64}",
                        }
                    )
                else:
                    # Tambahan catatan untu NISN tidak valid
                    qr_results.append(
                        {
                            "nis": student["nis"],
                            "nama": student["nama"],
                            "kelas": student["kelas"],
                            "error": f"NISN tid valid: {nisn_value}",
                            "qr_data": None,
                            "qr_image": None,
                        }
                    )
            else:
                # Jika siswa tidak ditemukan atau tidak punya NISN
                qr_results.append(
                    {
                        "nis": nis,
                        "error": "Siswa tidak ditemukan atau tidak memiliki NISN",
                        "qr_data": None,
                        "qr_image": None,
                    }
                )
        cursor.close()
        conn.close()
        # Hitung sukses dan gagal
        success_count = len([r for r in qr_results if "qr_data" in r and r["qr_data"]])
        error_count = len([r for r in qr_results if "error" in r])
        return jsonify(
            {
                "success": True,
                "count": len(qr_results),
                "success_count": success_count,
                "error_count": error_count,
                "qr_codes": qr_results,
            }
        )

    except Exception as e:
        logger.error(f"Bulk QR generation error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# TABLE STRUCTURE
@app.route("/api/debug/table-structure", methods=["GET"])
def debug_table_structure():
    """Debug endpoint to check table structure"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Cek struktur tabel siswa
        cursor.execute("DESCRIBE siswa")
        siswa_structure = cursor.fetchall()

        # Cek beberapa data sample
        cursor.execute("SELECT nis, nisn, nama, kelas, card_version FROM siswa LIMIT 5")
        sample_data = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "siswa_structure": siswa_structure,
                "sample_data": sample_data,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# CHECK NISN - GET
@app.route("/api/students/check-nisn", methods=["GET"])
@token_required
def check_student_nisn():
    """Check if students have valid NISN"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                nis,
                nisn,
                nama,
                kelas,
                CASE
                    WHEN nisn IS NULL OR nisn = '' THEN 'TIDAK ADA'
                    WHEN LENGTH(TRIM(nisn)) != 10 THEN 'TIDAK VALID'
                    WHEN TRIM(nisn) NOT REGEXP '^[0-9]{10}$' THEN 'TIDAK VALID'
                    ELSE 'VALID'
                END as status_nisn,
                LENGTH(TRIM(nisn)) as panjang_nisn
            FROM siswa
            ORDER BY kelas, nama
        """
        )

        students = cursor.fetchall()

        cursor.close()
        conn.close()

        # Hitung statistik
        valid_count = len([s for s in students if s["status_nisn"] == "VALID"])
        invalid_count = len([s for s in students if s["status_nisn"] == "TIDAK VALID"])
        missing_count = len([s for s in students if s["status_nisn"] == "TIDAK ADA"])

        return jsonify(
            {
                "success": True,
                "total": len(students),
                "valid_nisn": valid_count,
                "invalid_nisn": invalid_count,
                "missing_nisn": missing_count,
                "students": students,
            }
        )

    except Exception as e:
        logger.error(f"Check NISN error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# SCAN NISN - POST
@app.route("/api/scan-nisn", methods=["POST"])
def process_scan_nisn():
    """Process barcode scan based on NISN (legacy support)"""
    try:
        data = request.get_json()

        if not data or "nisn" not in data:
            return jsonify({"success": False, "message": "NISN diperlukan"}), 400

        nisn = str(data["nisn"]).strip()
        location = data.get("location", "Scanner NISN USB")

        # Validasi format NISN
        if len(nisn) != 10 or not nisn.isdigit():
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"NISN harus 10 digit angka. Diterima: {nisn}",
                    }
                ),
                400,
            )

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Find student by NISN
        cursor.execute("SELECT * FROM siswa WHERE nisn = %s", (nisn,))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Siswa dengan NISN {nisn} tidak ditemukan",
                    }
                ),
                404,
            )

        # Check attendance
        today = date.today()
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (student["id"], today),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f'{student["nama"]} sudah absen hari ini',
                    }
                ),
                409,
            )

        # Save attendance
        now = datetime.now()
        cursor.execute(
            """INSERT INTO absensi 
               (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                student["id"],
                student["nis"],
                today,
                now.time(),
                "Hadir",
                "scanner",
                location,
            ),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Absensi NISN berhasil",
                "student": {
                    "nis": student["nis"],
                    "nisn": student["nisn"],
                    "nama": student["nama"],
                    "kelas": student["kelas"],
                },
                "attendance": {
                    "date": str(today),
                    "time": now.strftime("%H:%M:%S"),
                    "method": "Scanner NISN",
                },
            }
        )

    except Exception as e:
        logger.error(f"NISN scan processing error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# SCANNER ENDPOINTS (Backward Compatibility)
# ===========================================


@app.route("/api/scan", methods=["POST"])
def process_scan():
    """Process barcode scan (legacy support)"""
    try:
        data = request.get_json()

        if not data or "nis" not in data:
            return jsonify({"success": False, "message": "NIS diperlukan"}), 400

        nis = str(data["nis"]).strip()
        location = data.get("location", "Scanner USB")

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Find student
        cursor.execute("SELECT * FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Siswa dengan NIS {nis} tidak ditemukan",
                    }
                ),
                404,
            )

        # Check attendance
        today = date.today()
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (student["id"], today),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f'{student["nama"]} sudah absen hari ini',
                    }
                ),
                409,
            )

        # Save attendance
        now = datetime.now()
        cursor.execute(
            """INSERT INTO absensi 
               (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                student["id"],
                student["nis"],
                today,
                now.time(),
                "Hadir",
                "Scanner",
                location,
            ),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Absensi berhasil",
                "student": {
                    "nis": student["nis"],
                    "nama": student["nama"],
                    "kelas": student["kelas"],
                },
                "attendance": {
                    "date": str(today),
                    "time": now.strftime("%H:%M:%S"),
                    "method": "Scanner",
                },
            }
        )

    except Exception as e:
        logger.error(f"Scan processing error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# STUDENT MANAGEMENT ENDPOINTS
# ===========================================


@app.route("/api/students", methods=["GET"])
@token_required
def get_students():
    """Get all students with optional filtering"""
    try:
        kelas = request.args.get("kelas")

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        if kelas:
            cursor.execute(
                "SELECT id, nis, nisn, nama, kelas FROM siswa WHERE kelas = %s ORDER BY nama",
                (kelas,),
            )
        else:
            cursor.execute(
                "SELECT id, nis, nisn, nama, kelas FROM siswa ORDER BY kelas, nama"
            )

        students = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "count": len(students), "students": students})

    except Exception as e:
        logger.error(f"Get students error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# DETAIL SISWA - GET
@app.route('/api/students/<nis>', methods=['GET'])
@token_required
def get_student_detail(nis):
    """Get detailed student information including attendance statistics"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)

        # Get student data
        cursor.execute(
            """SELECT id, nis, nisn, nama, kelas, card_version 
               FROM siswa 
               WHERE nis = %s""",
            (nis,)
        )
        
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': f'Siswa dengan NIS {nis} tidak ditemukan'
            }), 404

        # Get attendance statistics - PERBAIKAN: Handle NULL values dengan COALESCE
        cursor.execute(
            """SELECT 
                COUNT(*) as total_attendance,
                COUNT(CASE WHEN status = 'Hadir' THEN 1 END) as hadir,
                COUNT(CASE WHEN status = 'Izin' THEN 1 END) as izin,
                COUNT(CASE WHEN status = 'Sakit' THEN 1 END) as sakit,
                COUNT(CASE WHEN status = 'Alpha' THEN 1 END) as alpha,
                MAX(tanggal) as last_attendance_date
               FROM absensi 
               WHERE siswa_id = %s""",
            (student['id'],)
        )
        
        stats = cursor.fetchone()
        
        # PERBAIKAN: Konversi nilai None menjadi 0 untuk statistik
        if stats:
            stats = {
                'total_attendance': stats['total_attendance'] if stats['total_attendance'] is not None else 0,
                'hadir': stats['hadir'] if stats['hadir'] is not None else 0,
                'izin': stats['izin'] if stats['izin'] is not None else 0,
                'sakit': stats['sakit'] if stats['sakit'] is not None else 0,
                'alpha': stats['alpha'] if stats['alpha'] is not None else 0,
                'last_attendance_date': str(stats['last_attendance_date']) if stats['last_attendance_date'] else None
            }

        # Get recent attendance (last 10 records) - PERBAIKAN: Konversi semua ke string
        cursor.execute(
            """SELECT tanggal, waktu, status, metode, scanner_lokasi 
               FROM absensi 
               WHERE siswa_id = %s 
               ORDER BY tanggal DESC, waktu DESC 
               LIMIT 10""",
            (student['id'],)
        )
        
        recent_attendance_raw = cursor.fetchall()
        
        # PERBAIKAN: Konversi semua field ke tipe yang bisa di-serialize
        recent_attendance = []
        for att in recent_attendance_raw:
            recent_attendance.append({
                'tanggal': str(att['tanggal']) if att['tanggal'] else None,
                'waktu': str(att['waktu']) if att['waktu'] else None,
                'status': str(att['status']) if att['status'] else None,
                'metode': str(att['metode']) if att['metode'] else None,
                'scanner_lokasi': str(att['scanner_lokasi']) if att['scanner_lokasi'] else None
            })

        # Check if already attended today
        today = date.today()
        cursor.execute(
            "SELECT id FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (student['id'], today)
        )
        attended_today = cursor.fetchone() is not None

        cursor.close()
        conn.close()

        # PERBAIKAN: Konversi student data ke tipe yang bisa di-serialize
        student_data = {
            'id': int(student['id']) if student['id'] else None,
            'nis': str(student['nis']) if student['nis'] else '',
            'nisn': str(student['nisn']) if student['nisn'] else '',
            'nama': str(student['nama']) if student['nama'] else '',
            'kelas': str(student['kelas']) if student['kelas'] else '',
            'card_version': int(student['card_version']) if student['card_version'] else 1
        }

        return jsonify({
            'success': True,
            'student': student_data,
            'statistics': stats if stats else {
                'total_attendance': 0,
                'hadir': 0,
                'izin': 0,
                'sakit': 0,
                'alpha': 0,
                'last_attendance_date': None
            },
            'attended_today': attended_today,
            'recent_attendance': recent_attendance
        })

    except Exception as e:
        logger.error(f"Get student detail error: {e}")
        # PERBAIKAN: Kembalikan error dengan format JSON yang valid
        return jsonify({
            'success': False, 
            'message': f'Error: {str(e)}'
        }), 500


# TAMBAH SISWA - POST
@app.route("/api/students/add", methods=["POST"])
@token_required
def add_student():
    """Add new student"""
    try:
        data = request.get_json()

        required_fields = ["nis", "nisn", "nama", "kelas"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"success": False, "message": f"{field} diperlukan"}),
                    400,
                )

        nis = data["nis"].strip()
        nisn = data["nisn"].strip()
        nama = data["nama"].strip()
        kelas = data["kelas"].strip()

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Check if NIS already exists
        cursor.execute("SELECT id FROM siswa WHERE nis = %s", (nis,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "NIS sudah terdaftar"}), 409

        # Insert new student
        cursor.execute(
            "INSERT INTO siswa (nis, nisn, nama, kelas) VALUES (%s, %s, %s, %s)",
            (nis, nisn, nama, kelas),
        )

        conn.commit()
        student_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Siswa berhasil ditambahkan",
                "student": {
                    "id": student_id,
                    "nis": nis,
                    "nisn": nisn,
                    "nama": nama,
                    "kelas": kelas,
                },
            }
        )

    except Exception as e:
        logger.error(f"Add student error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# UPDATE data siswa
@app.route("/api/students/<nis>", methods=["PUT"])
@token_required
def update_student(nis):
    """Update student data"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "Data tidak ditemukan"}), 400

        nama = data.get("nama")
        kelas = data.get("kelas")

        if not nama or not kelas:
            return (
                jsonify({"success": False, "message": "Nama dan kelas diperlukan"}),
                400,
            )

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Cek apakah siswa ada
        cursor.execute("SELECT id FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Siswa tidak ditemukan"}), 404

        # Update data
        cursor.execute(
            "UPDATE siswa SET nama = %s, kelas = %s WHERE nis = %s",
            (nama.strip(), kelas.strip(), nis),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Data siswa berhasil diperbarui",
                "student": {"nis": nis, "nama": nama, "kelas": kelas},
            }
        )

    except Exception as e:
        logger.error(f"Update student error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# DELETE - data siswa
@app.route("/api/students/<nis>", methods=["DELETE"])
@token_required
def delete_student(nis):
    """Delete student"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Cek siswa
        cursor.execute("SELECT id, nama FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Siswa tidak ditemukan"}), 404

        # Hapus siswa
        cursor.execute("DELETE FROM siswa WHERE nis = %s", (nis,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify(
            {"success": True, "message": f"Siswa {student['nama']} berhasil dihapus"}
        )

    except mysql.connector.Error as db_err:
        logger.error(f"Delete student DB error: {db_err}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Gagal menghapus siswa. Periksa relasi data absensi.",
                }
            ),
            409,
        )

    except Exception as e:
        logger.error(f"Delete student error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# ATTENDANCE ENDPOINTS
# ===========================================


@app.route("/api/attendance/today", methods=["GET"])
@token_required
def get_today_attendance():
    """Get today's attendance"""
    try:
        kelas = request.args.get("kelas")
        status = request.args.get("status")

        today = date.today()

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT a.*, s.nama, s.kelas 
            FROM absensi a 
            JOIN siswa s ON a.siswa_id = s.id 
            WHERE a.tanggal = %s
        """
        params = [today]

        if kelas:
            query += " AND s.kelas = %s"
            params.append(kelas)

        if status:
            query += " AND a.status = %s"
            params.append(status)

        query += " ORDER BY a.waktu DESC"

        cursor.execute(query, tuple(params))
        attendance = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "date": str(today),
                "count": len(attendance),
                "attendance": attendance,
            }
        )

    except Exception as e:
        logger.error(f"Get attendance error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/attendance/statistics", methods=["GET"])
@token_required
def get_attendance_statistics():
    """Get attendance statistics"""
    try:
        start_date = request.args.get("start_date", date.today().isoformat())
        end_date = request.args.get("end_date", date.today().isoformat())

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Total students
        cursor.execute("SELECT COUNT(*) as total FROM siswa")
        total = cursor.fetchone()["total"]

        # Attendance by date
        cursor.execute(
            """
            SELECT 
                tanggal as date,
                COUNT(DISTINCT siswa_id) as attended,
                COUNT(CASE WHEN status = 'Hadir' THEN 1 END) as present,
                COUNT(CASE WHEN status = 'Izin' THEN 1 END) as izin,
                COUNT(CASE WHEN status = 'Sakit' THEN 1 END) as sick,
                COUNT(CASE WHEN status = 'Alpha' THEN 1 END) as alpha
            FROM absensi 
            WHERE tanggal BETWEEN %s AND %s
            GROUP BY tanggal
            ORDER BY tanggal DESC
        """,
            (start_date, end_date),
        )

        daily_stats = cursor.fetchall()

        # Attendance by class
        cursor.execute(
            """
            SELECT 
                s.kelas,
                COUNT(DISTINCT a.siswa_id) as attended,
                COUNT(*) as total_records
            FROM siswa s
            LEFT JOIN absensi a ON s.id = a.siswa_id AND a.tanggal = %s
            GROUP BY s.kelas
            ORDER BY s.kelas
        """,
            (date.today(),),
        )

        class_stats = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "total_students": total,
                "daily_statistics": daily_stats,
                "class_statistics": class_stats,
                "period": {"start_date": start_date, "end_date": end_date},
            }
        )

    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# SYSTEM ENDPOINTS
# ===========================================


@app.route("/api/system/info", methods=["GET"])
@token_required
def system_info():
    """Get system information"""
    try:
        import platform
        import psutil
        import socket

        # System info
        system_info = {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "architecture": platform.machine(),
        }

        # CPU info
        cpu_info = {
            "cores": psutil.cpu_count(),
            "usage_percent": psutil.cpu_percent(interval=1),
        }

        # Memory info
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_percent": memory.percent,
        }

        # Disk info
        disk = psutil.disk_usage("/")
        disk_info = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_percent": disk.percent,
        }

        # Database info
        conn = connect_db()
        if conn:
            cursor = conn.cursor(dictionary=True)

            # Counts
            cursor.execute("SELECT COUNT(*) as total FROM siswa")
            student_count = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM absensi")
            attendance_count = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM users")
            user_count = cursor.fetchone()["total"]

            cursor.close()
            conn.close()

            db_info = {
                "connected": True,
                "student_count": student_count,
                "attendance_count": attendance_count,
                "user_count": user_count,
            }
        else:
            db_info = {"connected": False}

        return jsonify(
            {
                "success": True,
                "system": system_info,
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "database": db_info,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"System info error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/system/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Check database
        conn = connect_db()
        db_status = "healthy" if conn else "unhealthy"
        if conn:
            conn.close()

        # Check QR secret
        qr_status = (
            "healthy"
            if QR_SECRET_KEY and QR_SECRET_KEY != "YOUR_SECRET_KEY_HERE"
            else "unhealthy"
        )

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "database": db_status,
                    "qr_secret": qr_status,
                    "api": "healthy",
                },
                "version": "1.0.0",
            }
        )

    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/api/test", methods=["GET"])
def test_api():
    """Test endpoint"""
    return jsonify(
        {
            "success": True,
            "message": "Absensi API is running",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "features": ["QR Code", "JWT Auth", "Scanner", "Attendance", "Students"],
        }
    )


# ===========================================
# DEBUGS ENDPOINT
# ===========================================
# 1. LOG VIEWER - Endpoint
# Endpoint untuk log
@app.route("/api/debug/logs", methods=["GET"])
@token_required
def get_logs():
    """Get application logs"""
    try:
        lines = request.args.get("lines", 100, type=int)

        log_file = "app.log"  # Sesuaikan dengan lokasi log

        if not os.path.exists(log_file):
            return jsonify({"success": False, "message": "Log file not found"})

        with open(log_file, "r") as f:
            logs = f.readlines()[-lines:]

        return jsonify({"success": True, "logs": logs, "total_lines": len(logs)})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# 2. PERVORMANCE MONITOR - Endpoint
@app.route("/api/debug/performance", methods=["GET"])
@token_required
def check_performance():
    """Check database performance"""
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Check query performance
        queries = [
            "SHOW STATUS LIKE 'Questions'",
            "SHOW STATUS LIKE 'Slow_queries'",
            "SHOW VARIABLES LIKE 'long_query_time'",
        ]

        results = {}
        for query in queries:
            cursor.execute(query)
            results[query] = cursor.fetchall()

        # Get table sizes
        cursor.execute(
            """
            SELECT
                table_name,
                ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            ORDER BY size_mb DESC
        """
        )

        table_sizes = cursor.fetchall()

        return jsonify(
            {"success": True, "performance_stats": results, "table_sizes": table_sizes}
        )

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# DATA BACKUP & RESTORE TOOL
@app.route("/api/debug/backup", methods=["POST"])
@token_required
def create_backup():
    """Create database backup"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup/backup_{timestamp}.sql"

        # Ensure backup directory exists
        os.makedirs("backup", exist_ok=True)

        conn = connect_db()
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        with open(backup_file, "w") as f:
            for table in tables:
                table_name = table[0]

                # Get create table syntax
                cursor.execute(f"SHOW CREATE TABLE {table_name}")
                create_table = cursor.fetchone()[1]
                f.write(f"{create_table};\n\n")

                # Get data
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                if rows:
                    # Get column names
                    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                    columns = [col[0] for col in cursor.fetchall()]

                    for row in rows:
                        values = []
                        for value in row:
                            if value is None:
                                values.append("NULL")
                            elif isinstance(value, (int, float)):
                                values.append(str(value))
                            else:
                                values.append(f"'{value}'")

                        insert = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                        f.write(f"{insert}\n")

                    f.write("\n")

        return jsonify(
            {
                "success": True,
                "backup_file": backup_file,
                "tables": len(tables),
                "size": os.path.getsize(backup_file),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# ===========================================
# ERROR HANDLERS ============================
# ===========================================


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify(
            {"success": False, "message": "Endpoint not found", "path": request.path}
        ),
        404,
    )


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"success": False, "message": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"success": False, "message": "Internal server error"}), 500


# ===========================================
# APPLICATION STARTUP
# ===========================================


def create_directories():
    """Create necessary directories"""
    directories = [
        "/var/www/html/api/logs",
        "/var/www/html/api/qr_codes",
        "/var/www/html/api/backups",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


if __name__ == "__main__":
    # Create directories
    create_directories()

    # Log startup
    logger.info("=" * 50)
    logger.info("Starting Absensi API Server")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Host: {API_CONFIG['host']}:{API_CONFIG['port']}")
    logger.info(
        f"QR Secret Configured: {'Yes' if QR_SECRET_KEY != 'YOUR_SECRET_KEY_HERE' else 'No'}"
    )
    logger.info("=" * 50)

    # Run the application
    app.run(
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        debug=API_CONFIG["debug"],
        threaded=API_CONFIG["threaded"],
    )
