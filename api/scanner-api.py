#!/usr/bin/env python3
"""
API Lengkap untuk Sistem Absensi
"""

from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime, date
import json
import os

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'absensi_user',
    'password': 'pass123',
    'database': 'absensi_siswa'
}

def connect_db():
    """Connect to MySQL database"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# ===========================================
# ENDPOINT UTAMA
# ===========================================

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint - Cek apakah API berjalan"""
    return jsonify({
        'success': True,
        'message': 'Scanner API is running',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'GET /api/test': 'Test API',
            'POST /api/scan': 'Process barcode scan',
            'GET /api/students': 'Get all students',
            'GET /api/attendance/today': 'Get today attendance',
            'GET /api/statistics': 'Get statistics',
            'GET /api/student/<nis>': 'Get student by NIS'
        }
    })

@app.route('/api/scan', methods=['POST'])
def process_scan():
    """Process barcode scan from scanner"""
    try:
        # Get data from request
        data = request.get_json()
        
        # Debug log
        print(f"[API] Received scan request: {data}")
        
        # Validate input
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        if 'nis' not in data:
            return jsonify({'success': False, 'message': 'NIS is required'}), 400
        
        nis = str(data['nis']).strip()
        location = data.get('location', 'Unknown')
        
        if not nis:
            return jsonify({'success': False, 'message': 'NIS cannot be empty'}), 400
        
        # Connect to database
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # 1. Find student by NIS
        cursor.execute("SELECT * FROM siswa WHERE nis = %s", (nis,))
        siswa = cursor.fetchone()
        
        if not siswa:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': f'Siswa dengan NIS {nis} tidak ditemukan'
            }), 404
        
        # 2. Check if already attended today
        today = date.today()
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (siswa['id'], today)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': f'{siswa["nama"]} sudah absen hari ini',
                'student': {
                    'nis': siswa['nis'],
                    'nama': siswa['nama'],
                    'kelas': siswa['kelas']
                },
                'previous_attendance': {
                    'time': str(existing['waktu']),
                    'method': existing['metode']
                }
            }), 409  # 409 Conflict
        
        # 3. Save attendance
        now = datetime.now()
        cursor.execute(
            """INSERT INTO absensi 
               (siswa_id, nis, tanggal, waktu, status, metode, scanner_lokasi) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (siswa['id'], siswa['nis'], today, now.time(), 'Hadir', 'Scanner', location)
        )
        
        conn.commit()
        
        # Get the inserted record
        cursor.execute("SELECT LAST_INSERT_ID() as id")
        attendance_id = cursor.fetchone()['id']
        
        cursor.close()
        conn.close()
        
        # Success response
        return jsonify({
            'success': True,
            'message': 'Absensi berhasil',
            'attendance_id': attendance_id,
            'student': {
                'id': siswa['id'],
                'nis': siswa['nis'],
                'nama': siswa['nama'],
                'kelas': siswa['kelas']
            },
            'attendance': {
                'date': str(today),
                'time': now.strftime('%H:%M:%S'),
                'status': 'Hadir',
                'method': 'Scanner',
                'location': location
            },
            'timestamp': now.isoformat()
        })
        
    except mysql.connector.Error as db_err:
        print(f"[API] Database error: {db_err}")
        return jsonify({
            'success': False, 
            'message': f'Database error: {db_err}'
        }), 500
        
    except Exception as e:
        print(f"[API] Unexpected error: {e}")
        return jsonify({
            'success': False, 
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = conn.cursor(dictionary=True)
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
        print(f"Error getting students: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/student/<nis>', methods=['GET'])
def get_student(nis):
    """Get student by NIS"""
    try:
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if student:
            return jsonify({
                'success': True,
                'student': student
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404
            
    except Exception as e:
        print(f"Error getting student: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/attendance/today', methods=['GET'])
def get_today_attendance():
    """Get today's attendance records"""
    try:
        today = date.today()
        
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, s.nama, s.kelas 
            FROM absensi a 
            JOIN siswa s ON a.siswa_id = s.id 
            WHERE a.tanggal = %s 
            ORDER BY a.waktu DESC
        """, (today,))
        
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
        print(f"Error getting attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get attendance statistics"""
    try:
        today = date.today()
        
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Total students
        cursor.execute("SELECT COUNT(*) as total FROM siswa")
        total_students = cursor.fetchone()['total']
        
        # Today's attendance
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT siswa_id) as attended,
                COUNT(CASE WHEN status = 'Hadir' THEN 1 END) as present,
                COUNT(CASE WHEN status = 'Izin' THEN 1 END) as izin,
                COUNT(CASE WHEN status = 'Sakit' THEN 1 END) as sick,
                COUNT(CASE WHEN status = 'Alpha' THEN 1 END) as alpha
            FROM absensi 
            WHERE tanggal = %s
        """, (today,))
        
        today_stats = cursor.fetchone()
        
        # Attendance by scanner location
        cursor.execute("""
            SELECT 
                COALESCE(scanner_lokasi, 'Manual') as location,
                COUNT(*) as count
            FROM absensi 
            WHERE tanggal = %s
            GROUP BY scanner_lokasi
        """, (today,))
        
        by_location = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'date': str(today),
            'statistics': {
                'total_students': total_students,
                'attended_today': today_stats['attended'] or 0,
                'present': today_stats['present'] or 0,
                'izin': today_stats['izin'] or 0,
                'sick': today_stats['sick'] or 0,
                'alpha': today_stats['alpha'] or 0,
                'absent': total_students - (today_stats['attended'] or 0),
                'attendance_rate': round((today_stats['attended'] or 0) / total_students * 100, 1) if total_students > 0 else 0
            },
            'by_location': by_location
        })
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check/<nis>', methods=['GET'])
def check_attendance(nis):
    """Check if student has attended today"""
    try:
        today = date.today()
        
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get student info
        cursor.execute("SELECT id, nis, nama, kelas FROM siswa WHERE nis = %s", (nis,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404
        
        # Check attendance
        cursor.execute("""
            SELECT * FROM absensi 
            WHERE siswa_id = %s AND tanggal = %s
        """, (student['id'], today))
        
        attendance = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'student': student,
            'has_attended': attendance is not None,
            'attendance': attendance
        })
        
    except Exception as e:
        print(f"Error checking attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = connect_db()
        if conn:
            conn.close()
            db_status = 'connected'
        else:
            db_status = 'disconnected'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_status,
            'service': 'absensi-scanner-api'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# ===========================================
# ERROR HANDLERS
# ===========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'message': 'Method not allowed'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

# ===========================================
# MAIN ENTRY POINT
# ===========================================

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Absensi Scanner API")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: http://192.168.1.11")
    print("Available endpoints:")
    print("  GET  /api/test          - Test API")
    print("  POST /api/scan          - Process scan")
    print("  GET  /api/students      - Get all students")
    print("  GET  /api/statistics    - Get statistics")
    print("  GET  /api/health        - Health check")
    print("=" * 50)

    # app.run(host='192.168.1.11', port=80, debug=True) 
    app.run(host='0.0.0.0', port=8080, debug=True)
