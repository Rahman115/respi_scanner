#!/usr/bin/env python3
"""
API Absensi dengan Flask-CORS
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime, date
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ===========================================
# KONFIGURASI CORS - SANGAT PENTING!
# ===========================================
# Izinkan semua origin untuk development
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Atau lebih spesifik untuk production:
# CORS(app, resources={
#     r"/api/*": {
#         "origins": ["http://192.168.1.11", "http://localhost"],
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization"],
#         "supports_credentials": True,
#         "max_age": 3600
#     }
# })

# Database configuration - SESUAIKAN DENGAN SETUP ANDA
db_config = {
    'host': 'localhost',
    'user': 'absensi_user',      # Ganti jika berbeda
    'password': 'pass123',       # Ganti dengan password Anda
    'database': 'absensi_siswa', # Ganti dengan nama database
    'port': 3306
}

def connect_db():
    """Connect to MySQL database"""
    try:
        conn = mysql.connector.connect(**db_config)
        logger.info("Database connected successfully")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None

# ===========================================
# ENDPOINT UTAMA
# ===========================================

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint"""
    logger.info("Test endpoint accessed")
    return jsonify({
        'success': True,
        'message': 'API Absensi berjalan dengan CORS!',
        'timestamp': datetime.now().isoformat(),
        'cors': 'enabled',
        'database': 'MySQL',
        'version': '1.0'
    })

@app.route('/api/scan', methods=['POST', 'OPTIONS'])
def process_scan():
    """Process barcode scan"""
    
    logger.info(f"Scan endpoint called with method: {request.method}")
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        logger.info("Handling OPTIONS preflight request")
        response = jsonify({'status': 'preflight'})
        return response
    
    try:
        # Parse JSON data
        if not request.is_json:
            logger.warning("Request is not JSON")
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        # Validate required fields
        if not data or 'nis' not in data:
            logger.warning("Missing 'nis' in request")
            return jsonify({
                'success': False,
                'message': 'NIS is required in JSON body'
            }), 400
        
        nis = str(data['nis']).strip()
        if not nis:
            return jsonify({
                'success': False,
                'message': 'NIS cannot be empty'
            }), 400
        
        # Connect to database
        conn = connect_db()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # TEST: Cek apakah tabel ada
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        logger.info(f"Available tables: {tables}")
        
        # 1. Cari siswa berdasarkan NIS
        cursor.execute("SELECT * FROM siswa WHERE nis = %s", (nis,))
        siswa = cursor.fetchone()
        
        if not siswa:
            cursor.close()
            conn.close()
            logger.warning(f"Student with NIS {nis} not found")
            return jsonify({
                'success': False,
                'message': f'Siswa dengan NIS {nis} tidak ditemukan'
            }), 404
        
        logger.info(f"Student found: {siswa['nama']}")
        
        # 2. Cek apakah sudah absen hari ini
        today = date.today()
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (siswa['id'], today)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            logger.info(f"Student {siswa['nama']} already attended today")
            return jsonify({
                'success': False,
                'message': f'{siswa["nama"]} sudah absen hari ini',
                'student': {
                    'nis': siswa['nis'],
                    'nama': siswa['nama'],
                    'kelas': siswa['kelas']
                },
                'attendance_time': str(existing['waktu']) if 'waktu' in existing else 'Unknown'
            }), 409
        
        # 3. Simpan absensi
        now = datetime.now()
        cursor.execute(
            """INSERT INTO absensi 
               (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (siswa['id'], siswa['nis'], today, now.time(), 'Hadir', 'Scanner', 'Ruang Scan')
        )
        
        conn.commit()
        
        # Get inserted ID
        cursor.execute("SELECT LAST_INSERT_ID() as id")
        attendance_id = cursor.fetchone()['id']
        
        cursor.close()
        conn.close()
        
        logger.info(f"Attendance saved for {siswa['nama']}, ID: {attendance_id}")
        
        # Success response
        return jsonify({
            'success': True,
            'message': 'Absensi berhasil dicatat',
            'attendance_id': attendance_id,
            'siswa': {
                'id': siswa['id'],
                'nis': siswa['nis'],
                'nama': siswa['nama'],
                'kelas': siswa['kelas']
            },
            'absensi': {
                'tanggal': str(today),
                'waktu': now.strftime('%H:%M:%S'),
                'status': 'Hadir',
                'metode': 'Scanner'
            },
            'timestamp': now.isoformat()
        })
        
    except mysql.connector.Error as db_err:
        logger.error(f"Database error: {db_err}")
        return jsonify({
            'success': False,
            'message': f'Database error: {db_err}'
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/check-db', methods=['GET'])
def check_database():
    """Check database connection and tables"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Cannot connect to database'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = [list(table.values())[0] for table in cursor.fetchall()]
        
        # Check students count
        cursor.execute("SELECT COUNT(*) as count FROM siswa")
        student_count = cursor.fetchone()['count']
        
        # Check today's attendance
        today = date.today()
        cursor.execute("SELECT COUNT(*) as count FROM absensi WHERE tanggal = %s", (today,))
        attendance_count = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'database': db_config['database'],
            'tables': tables,
            'statistics': {
                'total_siswa': student_count,
                'absensi_hari_ini': attendance_count
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===========================================
# ENDPOINT TANPA DATABASE (UNTUK TESTING)
# ===========================================

@app.route('/api/simple-scan', methods=['POST'])
def simple_scan():
    """Simple scan endpoint without database for testing"""
    try:
        data = request.get_json()
        nis = data.get('nis', 'unknown')
        
        return jsonify({
            'success': True,
            'message': 'Scan test berhasil (tanpa database)',
            'test_data': {
                'nis_diterima': nis,
                'nama': 'Siswa Test',
                'kelas': 'XII IPA 1',
                'waktu': datetime.now().strftime('%H:%M:%S')
            },
            'note': 'Ini hanya test, data tidak disimpan ke database'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===========================================
# ERROR HANDLERS
# ===========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint tidak ditemukan',
        'path': request.path
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

# ===========================================
# MAIN
# ===========================================

if __name__ == '__main__':
    print("=" * 60)
    print("ABSENSI API with CORS - Raspberry Pi")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {db_config['database']}")
    print(f"Host: {db_config['host']}")
    print(f"User: {db_config['user']}")
    print("=" * 60)
    print("Endpoints:")
    print("  GET  /api/test           - Test API")
    print("  POST /api/scan           - Process scan (with DB)")
    print("  POST /api/simple-scan    - Test scan (no DB)")
    print("  GET  /api/check-db       - Check database")
    print("=" * 60)
    print(f"Running on: http://0.0.0.0:8080")
    print(f"          : http://192.168.1.11:8080")
    print("=" * 60)
    
    # Jalankan dengan reloader disabled untuk production
    app.run(
        host='0.0.0.0', 
        port=8080, 
        debug=True,
        threaded=True
    )
