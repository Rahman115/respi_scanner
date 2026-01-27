# /var/www/html/api/scanner_api.py
#!/usr/bin/env python3
"""
API untuk handle scanner input
"""

from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime
import sys
import os

# Setup Flask
app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'absensi_user',
    'password': 'password123',
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

@app.route('/api/scan', methods=['POST'])
def process_scan():
    """Process barcode scan from scanner"""
    try:
        # Get NIS from request
        data = request.get_json()
        if not data or 'nis' not in data:
            return jsonify({'success': False, 'message': 'NIS tidak ditemukan'})
        
        nis = data['nis'].strip()
        
        # Connect to database
        conn = connect_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'})
        
        cursor = conn.cursor(dictionary=True)
        
        # 1. Cari siswa
        cursor.execute("SELECT * FROM siswa WHERE nis = %s", (nis,))
        siswa = cursor.fetchone()
        
        if not siswa:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': f'Siswa dengan NIS {nis} tidak ditemukan'})
        
        # 2. Cek apakah sudah absen hari ini
        today = datetime.now().date()
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = %s AND tanggal = %s",
            (siswa['id'], today)
        )
        sudah_absen = cursor.fetchone()
        
        if sudah_absen:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'message': f'{siswa["nama"]} sudah absen hari ini'
            })
        
        # 3. Simpan absensi
        now = datetime.now()
        cursor.execute(
            "INSERT INTO absensi (siswa_id, nis, tanggal, waktu, status, metode) VALUES (%s, %s, %s, %s, %s, %s)",
            (siswa['id'], siswa['nis'], today, now.time(), 'Hadir', 'Scanner')
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Absensi berhasil',
            'siswa': {
                'nis': siswa['nis'],
                'nama': siswa['nama'],
                'kelas': siswa['kelas'],
                'waktu': now.strftime('%H:%M:%S')
            }
        })
        
    except Exception as e:
        print(f"Error processing scan: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test API endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'Scanner API is working',
        'time': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
