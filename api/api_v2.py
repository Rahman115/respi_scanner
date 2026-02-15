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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/www/html/api/logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# JWT Configuration
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

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
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]

            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated

def generate_qr_signature(data):
    """Generate HMAC signature for QR code data"""
    message = json.dumps(data, sort_keys=True).encode()
    signature = hmac.new(
        QR_SECRET_KEY.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_qr_signature(data, signature):
    """Verify QR code signature"""
    expected_signature = generate_qr_signature(data)
    return hmac.compare_digest(expected_signature, signature)

# ===========================================
# AUTHENTICATION ENDPOINTS
# ===========================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint for admin/teachers"""
    try:
        data = request.get_json()

        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'success': False, 'message': 'Username dan password diperlukan'}), 400

        username = data['username']
        password = data['password']

        # Hash password (MD5 for compatibility with PHP)
        import hashlib
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, nama, role FROM users WHERE username = %s AND password = %s",
            (username, hashed_password)
        )

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'username': user['username'],
                'nama': user['nama'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, JWT_SECRET_KEY, algorithm='HS256')

            return jsonify({
                'success': True,
                'message': 'Login berhasil',
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'nama': user['nama'],
                    'role': user['role']
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Username atau password salah'}), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ===========================================
# QR CODE ENDPOINTS
# ===========================================

@app.route('/api/qr/generate/<nis>', methods=['GET'])
@token_required
def generate_qr_code(nis):
    """Generate QR code for student"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nis, nama, kelas, card_version FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        if not student:
            return jsonify({'success': False, 'message': 'Siswa tidak ditemukan'}), 404

        # Prepare QR data
        qr_data = {
            'type': 'student_card',
            'nis': student['nis'],
            # 'nama': student['nama'],
            # 'kelas': student['kelas'],
            'student_id': student['id'],
            'card_version':student['card_version']
            # 'issued_at': datetime.utcnow().isoformat()
            # 'expires': (datetime.utcnow() + timedelta(days=30)).isoformat()
        }

        # Generate signature
        signature = generate_qr_signature(qr_data)
        qr_data['signature'] = signature

        # Convert to string
        qr_string = json.dumps(qr_data)

        # Generate QR code
        qr = qrcode.QRCode(
            version=QR_CONFIG['version'],
            error_correction=getattr(qrcode.constants, f"ERROR_CORRECT_{QR_CONFIG['error_correction']}"),
            box_size=QR_CONFIG['box_size'],
            border=QR_CONFIG['border']
        )

        qr.add_data(qr_string)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Convert to base64
        qr_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

        return jsonify({
            'success': True,
            'student': {
                'nis': student['nis'],
                'nama': student['nama'],
                'kelas': student['kelas']
            },
            'qr_data': qr_data,
            'qr_image': f"data:image/png;base64,{qr_base64}"
            # 'expires': qr_data['expires']
        })

    except Exception as e:
        logger.error(f"QR generation error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/qr/verify', methods=['POST'])
def verify_qr_code():
    """Verify and process QR code scan"""
    try:
        data = request.get_json()

        if not data or 'qr_data' not in data:
            return jsonify({'success': False, 'message': 'QR data diperlukan'}), 400

        qr_data = data['qr_data']

        # Debug log untuk melihat struktur data yang diterima
        logger.info(f"QR data received: {json.dumps(qr_data)}")

        logger.info(
            f"QR scan attempt - qr_data.get | NIS={qr_data.get('nis')} | IP={request.remote_addr}"
        )

        # Cek apakah nis ada dalam qr_data
        if 'nis' not in qr_data:
            logger.warning(f"QR data missing 'nis' field: {qr_data}")
            return jsonify({
                'success': False,
                'message': 'Data QR tidak valid: NIS tidak ditemukan'
            }), 400

        nis_value = qr_data.get('nis')

        logger.info(
            f"QR scan attempt - nis_value | NIS={nis_value} | IP={request.remote_addr}"
        )



        # Verify signature
        if 'signature' not in qr_data:
            return jsonify({'success': False, 'message': 'Signature tidak ditemukan'}), 400

        # signature = qr_data.pop('signature')
        # if not verify_qr_signature(qr_data, signature):
        signature = qr_data.get('signature')
        payload = qr_data.copy()
        payload.pop('signature',None)

        if not verify_qr_signature(payload, signature):
            logger.warning(
                f"Invalid QR signature | NIS={nis_value} | IP={request.remote_addr}"
            )
            return jsonify({'success': False, 'message': 'Signature tidak valid'}), 401

        # Check expiration
        # expires = datetime.fromisoformat(qr_data['expires'].replace('Z', '+00:00'))
        # if datetime.utcnow() > expires:
        #    return jsonify({'success': False, 'message': 'QR code sudah kadaluarsa'}), 400

        # changed code
        # < Database check >
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, nis, nama, kelas, card_version FROM siswa WHERE nis = %s",
            (nis_value,)
        )
        student = cursor.fetchone()

        if not student:
            logger.warning(
                f"QR scan with unknown NIS | NIS={nis_value} | IP={request.remote_addr}"
            )
            return jsonify({'success': False, 'message': 'Siswa tidak valid'}), 404

        # if student['aktif'] == 0:
        #     logger.warning(
        #         f"Inactive student card scanned | NIS={student['nis']} | IP={request.remote_addr}"
        #     )
        #     return jsonify({'success': False, 'message': 'Kartu siswa tidak aktif'}), 403

        # cek card_version

        if qr_data['card_version'] != student['card_version']:
            logger.warning(
                f"Outdated card version | NIS={student['nis']} "
                f"| QR={qr_data.get('card_version')} "
                f"| DB={student['card_version']} "
                f"| IP={request.remote_addr}"
            )
            return jsonify({
                'success': False,
                'message': 'Kartu siswa sudah tidak berlaku'
            }), 403


        # Process attendance
        nis = nis_value
        location = data.get('location', 'QR Scanner')

        # Connect to database
        # conn = connect_db()
        # if not conn:
        #     return jsonify({'success': False, 'message': 'Database error'}), 500

        # cursor = conn.cursor(dictionary=True)

        # Find student
        # cursor.execute("SELECT * FROM siswa WHERE nis = %s", (nis,))
        # student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Siswa tidak ditemukan'}), 404

        # Check if already attended today
        today = date.today()
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (student['id'], today)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': f'{student["nama"]} sudah absen hari ini',
                'student': {
                    'nis': student['nis'],
                    'nama': student['nama'],
                    'kelas': student['kelas']
                }
            }), 409

        # Save attendance
        now = datetime.now()
        cursor.execute(
            """INSERT INTO absensi
               (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (student['id'], student['nis'], today, now.time(), 'Hadir', 'scanner', location)
        )

        conn.commit()

        # Get the inserted record
        cursor.execute("SELECT LAST_INSERT_ID() as id")
        attendance_id = cursor.fetchone()['id']

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Absensi QR berhasil',
            'student': {
                'nis': student['nis'],
                'nama': student['nama'],
                'kelas': student['kelas']
            },
            'attendance': {
                'id': attendance_id,
                'date': str(today),
                'time': now.strftime('%H:%M:%S'),
                'method': 'QR Code',
                'location': location
            }
        })

    except Exception as e:
        logger.error(f"QR verification error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/qr/bulk/generate', methods=['POST'])
@token_required
def generate_bulk_qr():
    """Generate QR codes for multiple students"""
    try:
        data = request.get_json()

        if not data or 'nis_list' not in data:
            return jsonify({'success': False, 'message': 'List NIS diperlukan'}), 400

        nis_list = data['nis_list']

        if not isinstance(nis_list, list):
            return jsonify({'success': False, 'message': 'nis_list harus berupa array'}), 400

        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)

        qr_results = []

        for nis in nis_list:
            cursor.execute("SELECT id, nis, nama, kelas FROM siswa WHERE nis = %s", (nis,))
            student = cursor.fetchone()

            if student:
                # Generate QR data
                qr_data = {
                    'type': 'student_card',
                    'nis': student['nis'],
                    # 'nama': student['nama'],
                    # 'kelas': student['kelas'],
                    'student_id': student['id'],
                    'card_version': student['card_version']
                    # 'timestamp': datetime.utcnow().isoformat(),
                    # 'expires': (datetime.utcnow() + timedelta(days=30)).isoformat()
                }

                signature = generate_qr_signature(qr_data)
                qr_data['signature'] = signature
                qr_string = json.dumps(qr_data)

                # Generate QR code
                qr = qrcode.QRCode(
                    version=QR_CONFIG['version'],
                    error_correction=getattr(qrcode.constants, f"ERROR_CORRECT_{QR_CONFIG['error_correction']}"),
                    box_size=QR_CONFIG['box_size'],
                    border=QR_CONFIG['border']
                )

                qr.add_data(qr_string)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)

                qr_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

                qr_results.append({
                    'nis': student['nis'],
                    'nama': student['nama'],
                    'kelas': student['kelas'],
                    'qr_data': qr_data,
                    'qr_image': f"data:image/png;base64,{qr_base64}"
                })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'count': len(qr_results),
            'qr_codes': qr_results
        })

    except Exception as e:
        logger.error(f"Bulk QR generation error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500



@app.route('/api/debug/table-structure', methods=['GET'])
def debug_table_structure():
    """Debug endpoint to check table structure"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Cek struktur tabel siswa
        cursor.execute("DESCRIBE siswa")
        siswa_structure = cursor.fetchall()
        
        # Cek beberapa data sample
        cursor.execute("SELECT nis, nisn, nama, kelas, card_version FROM siswa LIMIT 5")
        sample_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'siswa_structure': siswa_structure,
            'sample_data': sample_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500





# ===========================================
# SCANNER ENDPOINTS (Backward Compatibility)
# ===========================================

@app.route('/api/scan', methods=['POST'])
def process_scan():
    """Process barcode scan (legacy support)"""
    try:
        data = request.get_json()

        if not data or 'nis' not in data:
            return jsonify({'success': False, 'message': 'NIS diperlukan'}), 400

        nis = str(data['nis']).strip()
        location = data.get('location', 'Scanner USB')

        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)

        # Find student
        cursor.execute("SELECT * FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': f'Siswa dengan NIS {nis} tidak ditemukan'
            }), 404

        # Check attendance
        today = date.today()
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (student['id'], today)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': f'{student["nama"]} sudah absen hari ini'
            }), 409
        
        # Save attendance
        now = datetime.now()
        cursor.execute(
            """INSERT INTO absensi 
               (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (student['id'], student['nis'], today, now.time(), 'Hadir', 'Scanner', location)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Absensi berhasil',
            'student': {
                'nis': student['nis'],
                'nama': student['nama'],
                'kelas': student['kelas']
            },
            'attendance': {
                'date': str(today),
                'time': now.strftime('%H:%M:%S'),
                'method': 'Scanner'
            }
        })
        
    except Exception as e:
        logger.error(f"Scan processing error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ===========================================
# STUDENT MANAGEMENT ENDPOINTS
# ===========================================

@app.route('/api/students', methods=['GET'])
@token_required
def get_students():
    """Get all students with optional filtering"""
    try:
        kelas = request.args.get('kelas')

        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)

        if kelas:
            cursor.execute(
                "SELECT id, nis, nama, kelas FROM siswa WHERE kelas = %s ORDER BY nama",
                (kelas,)
            )
        else:
            cursor.execute("SELECT id, nis, nama, kelas FROM siswa ORDER BY kelas, nama")

        students = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'count': len(students),
            'students': students
        })

    except Exception as e:
        logger.error(f"Get students error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/students/add', methods=['POST'])
@token_required
def add_student():
    """Add new student"""
    try:
        data = request.get_json()

        required_fields = ['nis', 'nama', 'kelas']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'{field} diperlukan'}), 400

        nis = data['nis'].strip()
        nama = data['nama'].strip()
        kelas = data['kelas'].strip()

        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)

        # Check if NIS already exists
        cursor.execute("SELECT id FROM siswa WHERE nis = %s", (nis,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'NIS sudah terdaftar'}), 409

        # Insert new student
        cursor.execute(
            "INSERT INTO siswa (nis, nama, kelas) VALUES (%s, %s, %s)",
            (nis, nama, kelas)
        )

        conn.commit()
        student_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Siswa berhasil ditambahkan',
            'student': {
                'id': student_id,
                'nis': nis,
                'nama': nama,
                'kelas': kelas
            }
        })

    except Exception as e:
        logger.error(f"Add student error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
# UPDATE data siswa
@app.route('/api/students/<nis>', methods=['PUT'])
@token_required
def update_student(nis):
    """Update student data"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 400

        nama = data.get('nama')
        kelas = data.get('kelas')

        if not nama or not kelas:
            return jsonify({'success': False, 'message': 'Nama dan kelas diperlukan'}), 400

        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)

        # Cek apakah siswa ada
        cursor.execute("SELECT id FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Siswa tidak ditemukan'}), 404

        # Update data
        cursor.execute(
            "UPDATE siswa SET nama = %s, kelas = %s WHERE nis = %s",
            (nama.strip(), kelas.strip(), nis)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Data siswa berhasil diperbarui',
            'student': {
                'nis': nis,
                'nama': nama,
                'kelas': kelas
            }
        })

    except Exception as e:
        logger.error(f"Update student error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# DELETE - data siswa
@app.route('/api/students/<nis>', methods=['DELETE'])
@token_required
def delete_student(nis):
    """Delete student"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cursor = conn.cursor(dictionary=True)

        # Cek siswa
        cursor.execute("SELECT id, nama FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Siswa tidak ditemukan'}), 404

        # Hapus siswa
        cursor.execute("DELETE FROM siswa WHERE nis = %s", (nis,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f"Siswa {student['nama']} berhasil dihapus"
        })

    except mysql.connector.Error as db_err:
        logger.error(f"Delete student DB error: {db_err}")
        return jsonify({
            'success': False,
            'message': 'Gagal menghapus siswa. Periksa relasi data absensi.'
        }), 409

    except Exception as e:
        logger.error(f"Delete student error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ===========================================
# ATTENDANCE ENDPOINTS
# ===========================================

@app.route('/api/attendance/today', methods=['GET'])
@token_required
def get_today_attendance():
    """Get today's attendance"""
    try:
        kelas = request.args.get('kelas')
        status = request.args.get('status')
        
        today = date.today()
        
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
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
        
        return jsonify({
            'success': True,
            'date': str(today),
            'count': len(attendance),
            'attendance': attendance
        })
        
    except Exception as e:
        logger.error(f"Get attendance error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/attendance/statistics', methods=['GET'])
@token_required
def get_attendance_statistics():
    """Get attendance statistics"""
    try:
        start_date = request.args.get('start_date', date.today().isoformat())
        end_date = request.args.get('end_date', date.today().isoformat())
        
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Total students
        cursor.execute("SELECT COUNT(*) as total FROM siswa")
        total = cursor.fetchone()['total']
        
        # Attendance by date
        cursor.execute("""
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
        """, (start_date, end_date))
        
        daily_stats = cursor.fetchall()
        
        # Attendance by class
        cursor.execute("""
            SELECT 
                s.kelas,
                COUNT(DISTINCT a.siswa_id) as attended,
                COUNT(*) as total_records
            FROM siswa s
            LEFT JOIN absensi a ON s.id = a.siswa_id AND a.tanggal = %s
            GROUP BY s.kelas
            ORDER BY s.kelas
        """, (date.today(),))
        
        class_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total_students': total,
            'daily_statistics': daily_stats,
            'class_statistics': class_stats,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ===========================================
# SYSTEM ENDPOINTS
# ===========================================

@app.route('/api/system/info', methods=['GET'])
@token_required
def system_info():
    """Get system information"""
    try:
        import platform
        import psutil
        import socket
        
        # System info
        system_info = {
            'hostname': socket.gethostname(),
            'os': platform.system(),
            'os_version': platform.version(),
            'python_version': platform.python_version(),
            'processor': platform.processor(),
            'architecture': platform.machine()
        }
        
        # CPU info
        cpu_info = {
            'cores': psutil.cpu_count(),
            'usage_percent': psutil.cpu_percent(interval=1)
        }
        
        # Memory info
        memory = psutil.virtual_memory()
        memory_info = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'used_percent': memory.percent
        }
        
        # Disk info
        disk = psutil.disk_usage('/')
        disk_info = {
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'used_percent': disk.percent
        }
        
        # Database info
        conn = connect_db()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Counts
            cursor.execute("SELECT COUNT(*) as total FROM siswa")
            student_count = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM absensi")
            attendance_count = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM users")
            user_count = cursor.fetchone()['total']
            
            cursor.close()
            conn.close()
            
            db_info = {
                'connected': True,
                'student_count': student_count,
                'attendance_count': attendance_count,
                'user_count': user_count
            }
        else:
            db_info = {'connected': False}
        
        return jsonify({
            'success': True,
            'system': system_info,
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'database': db_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"System info error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/system/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database
        conn = connect_db()
        db_status = 'healthy' if conn else 'unhealthy'
        if conn:
            conn.close()
        
        # Check QR secret
        qr_status = 'healthy' if QR_SECRET_KEY and QR_SECRET_KEY != 'YOUR_SECRET_KEY_HERE' else 'unhealthy'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': db_status,
                'qr_secret': qr_status,
                'api': 'healthy'
            },
            'version': '1.0.0'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint"""
    return jsonify({
        'success': True,
        'message': 'Absensi API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'features': ['QR Code', 'JWT Auth', 'Scanner', 'Attendance', 'Students']
    })

# ===========================================
# ERROR HANDLERS
# ===========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found',
        'path': request.path
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'message': 'Method not allowed'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

# ===========================================
# APPLICATION STARTUP
# ===========================================

def create_directories():
    """Create necessary directories"""
    directories = [
        '/var/www/html/api/logs',
        '/var/www/html/api/qr_codes',
        '/var/www/html/api/backups'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

if __name__ == '__main__':
    # Create directories
    create_directories()
    
    # Log startup
    logger.info("=" * 50)
    logger.info("Starting Absensi API Server")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Host: {API_CONFIG['host']}:{API_CONFIG['port']}")
    logger.info(f"QR Secret Configured: {'Yes' if QR_SECRET_KEY != 'YOUR_SECRET_KEY_HERE' else 'No'}")
    logger.info("=" * 50)
    
    # Run the application
    app.run(
        host=API_CONFIG['host'],
        port=API_CONFIG['port'],
        debug=API_CONFIG['debug'],
        threaded=API_CONFIG['threaded']
    )
