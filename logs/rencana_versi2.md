# **Implementasi Detail: Aplikasi Absensi Web dengan Flask & Auto-Start di Raspberry Pi**

## **Arsitektur Lengkap**

```
Raspberry Pi Boot → Apache2 + mod_wsgi → Flask App → 
Chromium Kiosk Mode → Siap Scan
```

## **1. INSTALASI & KONFIGURASI DASAR**

### **A. Update System & Install Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install packages
sudo apt install -y \
    apache2 \
    libapache2-mod-wsgi-py3 \
    python3-pip \
    python3-venv \
    chromium-browser \
    unclutter \
    git \
    zbar-tools \
    python3-opencv \
    libcamera-dev
```

### **B. Setup Virtual Environment**
```bash
# Buat directory aplikasi
sudo mkdir -p /var/www/absensi
cd /var/www/absensi

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install \
    flask \
    flask-sqlalchemy \
    flask-cors \
    opencv-python-headless \
    pyzbar \
    pillow \
    numpy \
    pandas
```

## **2. STRUKTUR APLIKASI FLASK**

```bash
/var/www/absensi/
├── absensi_app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── scanner.py
│   └── utils.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── scanner.js
│   └── images/
├── templates/
│   ├── index.html
│   ├── scanner.html
│   └── admin.html
├── venv/
├── absensi.wsgi
└── config.py
```

### **A. File Konfigurasi (`config.py`)**
```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-absensi-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'absensi.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CAMERA_INDEX = 0  # Index camera USB (biasanya 0)
    TIMEZONE = 'Asia/Jakarta'
```

### **B. Main Application (`absensi_app/__init__.py`)**
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Register blueprints/routes
    from absensi_app import routes
    app.register_blueprint(routes.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
```

### **C. Models (`absensi_app/models.py`)**
```python
from datetime import datetime
from absensi_app import db

class Siswa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nis = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(10), nullable=False)
    qr_code = db.Column(db.String(100), unique=True)
    foto = db.Column(db.String(200))
    
    absensi = db.relationship('Absensi', backref='siswa', lazy=True)

class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    siswa_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    waktu_masuk = db.Column(db.Time, nullable=False, default=datetime.utcnow().time)
    waktu_keluar = db.Column(db.Time)
    status = db.Column(db.String(20), default='Hadir')  # Hadir, Terlambat, Izin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('siswa_id', 'tanggal', name='unique_absensi_harian'),)
```

### **D. Scanner Module (`absensi_app/scanner.py`)**
```python
import cv2
from pyzbar.pyzbar import decode
from datetime import datetime
import time

class QRScanner:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.camera = None
        
    def start_camera(self):
        """Initialize camera"""
        self.camera = cv2.VideoCapture(self.camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return self.camera.isOpened()
    
    def scan_qr(self):
        """Capture and decode QR code"""
        if not self.camera or not self.camera.isOpened():
            if not self.start_camera():
                return None
        
        ret, frame = self.camera.read()
        if ret:
            # Convert to grayscale for better detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Decode QR codes
            decoded_objects = decode(gray)
            
            if decoded_objects:
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    return qr_data
        
        return None
    
    def release_camera(self):
        """Release camera resource"""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()
    
    def get_frame(self):
        """Get frame for streaming"""
        if not self.camera or not self.camera.isOpened():
            self.start_camera()
        
        ret, frame = self.camera.read()
        if ret:
            # Encode frame to JPEG
            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()
        return None
```

### **E. Routes (`absensi_app/routes.py`)**
```python
from flask import Blueprint, render_template, request, jsonify, Response
from datetime import datetime, time
from absensi_app import db
from absensi_app.models import Siswa, Absensi
from absensi_app.scanner import QRScanner
import json

bp = Blueprint('main', __name__)
scanner = QRScanner()

@bp.route('/')
def index():
    """Halaman utama scanning"""
    return render_template('scanner.html')

@bp.route('/scan', methods=['POST'])
def scan_qr():
    """API endpoint untuk scan QR"""
    qr_data = scanner.scan_qr()
    
    if qr_data:
        try:
            data = json.loads(qr_data)
            nis = data.get('nis')
            
            if nis:
                siswa = Siswa.query.filter_by(nis=nis).first()
                if siswa:
                    # Cek absensi hari ini
                    today = datetime.now().date()
                    absensi = Absensi.query.filter_by(
                        siswa_id=siswa.id, 
                        tanggal=today
                    ).first()
                    
                    if not absensi:
                        # Absensi masuk
                        absensi = Absensi(
                            siswa_id=siswa.id,
                            waktu_masuk=datetime.now().time(),
                            status='Hadir'
                        )
                        db.session.add(absensi)
                        db.session.commit()
                        
                        return jsonify({
                            'success': True,
                            'message': f'Absensi berhasil: {siswa.nama}',
                            'data': {
                                'nama': siswa.nama,
                                'kelas': siswa.kelas,
                                'waktu': datetime.now().strftime('%H:%M:%S'),
                                'status': 'Masuk'
                            }
                        })
                    else:
                        # Absensi pulang
                        if not absensi.waktu_keluar:
                            absensi.waktu_keluar = datetime.now().time()
                            db.session.commit()
                            
                            return jsonify({
                                'success': True,
                                'message': f'Pulang berhasil: {siswa.nama}',
                                'data': {
                                    'nama': siswa.nama,
                                    'kelas': siswa.kelas,
                                    'waktu': datetime.now().strftime('%H:%M:%S'),
                                    'status': 'Pulang'
                                }
                            })
                        else:
                            return jsonify({
                                'success': False,
                                'message': 'Sudah absen masuk dan pulang hari ini'
                            })
        except json.JSONDecodeError:
            return jsonify({'success': False, 'message': 'Format QR tidak valid'})
    
    return jsonify({'success': False, 'message': 'Tidak ada QR terdeteksi'})

@bp.route('/video_feed')
def video_feed():
    """Stream video camera untuk preview"""
    def generate():
        while True:
            frame = scanner.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            else:
                # Frame kosong jika camera error
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n\r\n')
    
    return Response(generate(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@bp.route('/api/absensi/hari-ini')
def absensi_hari_ini():
    """Get absensi hari ini"""
    today = datetime.now().date()
    absensi = Absensi.query.filter_by(tanggal=today).all()
    
    result = []
    for a in absensi:
        result.append({
            'nis': a.siswa.nis,
            'nama': a.siswa.nama,
            'kelas': a.siswa.kelas,
            'waktu_masuk': a.waktu_masuk.strftime('%H:%M:%S') if a.waktu_masuk else None,
            'waktu_keluar': a.waktu_keluar.strftime('%H:%M:%S') if a.waktu_keluar else None,
            'status': a.status
        })
    
    return jsonify(result)

@bp.route('/admin')
def admin():
    """Halaman admin untuk monitoring"""
    return render_template('admin.html')
```

## **3. TEMPLATE HTML & JAVASCRIPT**

### **A. Template Scanner (`templates/scanner.html`)**
```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Absensi QR Code - Sekolah XYZ</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            max-width: 1000px;
            width: 100%;
        }
        
        .header {
            background: #4a5568;
            color: white;
            padding: 25px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.2rem;
            margin-bottom: 5px;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 1.1rem;
        }
        
        .content {
            display: flex;
            flex-direction: column;
            padding: 0;
        }
        
        @media (min-width: 768px) {
            .content {
                flex-direction: row;
            }
        }
        
        .scanner-section {
            flex: 1;
            padding: 30px;
            background: #f7fafc;
            border-right: 1px solid #e2e8f0;
        }
        
        .info-section {
            flex: 1;
            padding: 30px;
        }
        
        .camera-container {
            position: relative;
            width: 100%;
            height: 300px;
            border-radius: 15px;
            overflow: hidden;
            background: #000;
            margin-bottom: 20px;
        }
        
        #video-feed {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .scan-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 200px;
            height: 200px;
            border: 3px solid #00ff00;
            border-radius: 10px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { border-color: #00ff00; }
            50% { border-color: transparent; }
            100% { border-color: #00ff00; }
        }
        
        .scan-btn {
            background: #48bb78;
            color: white;
            border: none;
            padding: 18px 40px;
            font-size: 1.2rem;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
            transition: background 0.3s;
            font-weight: bold;
            letter-spacing: 1px;
        }
        
        .scan-btn:hover {
            background: #38a169;
        }
        
        .scan-btn:active {
            transform: scale(0.98);
        }
        
        .result-container {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-top: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #4299e1;
            display: none;
        }
        
        .result-success {
            border-left-color: #48bb78;
        }
        
        .result-error {
            border-left-color: #f56565;
        }
        
        .result-title {
            font-size: 1.5rem;
            margin-bottom: 10px;
            color: #2d3748;
        }
        
        .result-message {
            color: #4a5568;
            font-size: 1.1rem;
            margin-bottom: 15px;
        }
        
        .student-info {
            background: #edf2f7;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #cbd5e0;
        }
        
        .info-row:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        
        .info-label {
            font-weight: bold;
            color: #4a5568;
        }
        
        .info-value {
            color: #2d3748;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        .status-masuk {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .status-pulang {
            background: #bee3f8;
            color: #2a4365;
        }
        
        .auto-scan-info {
            background: #fffaf0;
            border: 1px solid #fbd38d;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            text-align: center;
            color: #744210;
        }
        
        .clock {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2d3748;
            text-align: center;
            margin-bottom: 10px;
            font-family: 'Courier New', monospace;
        }
        
        .date {
            font-size: 1.2rem;
            color: #718096;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .recent-title {
            font-size: 1.3rem;
            color: #2d3748;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        #recent-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .recent-item {
            background: #f7fafc;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #4299e1;
        }
        
        .recent-name {
            font-weight: bold;
            color: #2d3748;
        }
        
        .recent-time {
            color: #718096;
            font-size: 0.9rem;
        }
        
        .recent-status {
            float: right;
            font-size: 0.8rem;
            padding: 3px 10px;
            border-radius: 12px;
        }
        
        footer {
            text-align: center;
            padding: 20px;
            background: #f7fafc;
            color: #718096;
            border-top: 1px solid #e2e8f0;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SISTEM ABSENSI QR CODE</h1>
            <p>SMA NEGERI 1 CONTOH - Silakan scan QR Code Anda</p>
        </div>
        
        <div class="content">
            <div class="scanner-section">
                <div class="clock" id="clock">00:00:00</div>
                <div class="date" id="date">-</div>
                
                <div class="camera-container">
                    <img id="video-feed" src="{{ url_for('video_feed') }}" alt="Camera Feed">
                    <div class="scan-overlay"></div>
                </div>
                
                <button class="scan-btn" id="scan-btn">
                    <span id="btn-text">SCAN QR CODE SEKARANG</span>
                    <span id="btn-loading" class="loading" style="display: none;"></span>
                </button>
                
                <div class="auto-scan-info">
                    <strong>Auto-scan aktif!</strong> Arahkan QR Code ke kamera dan sistem akan membaca secara otomatis.
                </div>
                
                <div class="result-container" id="result-container">
                    <div class="result-title" id="result-title">Hasil Scan</div>
                    <div class="result-message" id="result-message"></div>
                    <div class="student-info" id="student-info"></div>
                </div>
            </div>
            
            <div class="info-section">
                <h2 class="recent-title">📋 Absensi Terbaru</h2>
                <div id="recent-list">
                    <!-- List akan diisi oleh JavaScript -->
                    <div style="text-align: center; padding: 20px; color: #718096;">
                        Sedang memuat data...
                    </div>
                </div>
                
                <div style="margin-top: 30px;">
                    <h3 style="color: #4a5568; margin-bottom: 15px;">📊 Statistik Hari Ini</h3>
                    <div style="display: flex; gap: 15px;">
                        <div style="flex: 1; background: #c6f6d5; padding: 15px; border-radius: 10px; text-align: center;">
                            <div style="font-size: 2rem; font-weight: bold; color: #22543d;" id="stat-hadir">0</div>
                            <div style="color: #22543d;">Hadir</div>
                        </div>
                        <div style="flex: 1; background: #fed7d7; padding: 15px; border-radius: 10px; text-align: center;">
                            <div style="font-size: 2rem; font-weight: bold; color: #742a2a;" id="stat-belum">0</div>
                            <div style="color: #742a2a;">Belum Absen</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            Sistem Absensi QR Code © 2024 - SMA Negeri 1 Contoh
            <br>
            <small>Terakhir diperbarui: <span id="last-update">-</span></small>
        </footer>
    </div>

    <script src="{{ url_for('static', filename='js/scanner.js') }}"></script>
    <script>
        // Update clock
        function updateClock() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('id-ID');
            const dateStr = now.toLocaleDateString('id-ID', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            document.getElementById('clock').textContent = timeStr;
            document.getElementById('date').textContent = dateStr;
            document.getElementById('last-update').textContent = now.toLocaleString('id-ID');
        }
        
        // Load recent attendance
        async function loadRecentAttendance() {
            try {
                const response = await fetch('/api/absensi/hari-ini');
                const data = await response.json();
                
                const recentList = document.getElementById('recent-list');
                recentList.innerHTML = '';
                
                // Sort by latest
                data.sort((a, b) => {
                    const timeA = a.waktu_masuk || a.waktu_keluar || '';
                    const timeB = b.waktu_masuk || b.waktu_keluar || '';
                    return timeB.localeCompare(timeA);
                }).slice(0, 10).forEach(item => {
                    const recentItem = document.createElement('div');
                    recentItem.className = 'recent-item';
                    
                    const status = item.waktu_keluar ? 'Pulang' : 'Masuk';
                    const time = item.waktu_keluar || item.waktu_masuk;
                    
                    recentItem.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div class="recent-name">${item.nama}</div>
                                <div class="recent-time">Kelas ${item.kelas} • ${time}</div>
                            </div>
                            <span class="recent-status ${status === 'Masuk' ? 'status-masuk' : 'status-pulang'}">
                                ${status}
                            </span>
                        </div>
                    `;
                    
                    recentList.appendChild(recentItem);
                });
                
                // Update statistics
                const totalHadir = data.length;
                const totalSiswa = 100; // Ganti dengan total siswa sebenarnya
                document.getElementById('stat-hadir').textContent = totalHadir;
                document.getElementById('stat-belum').textContent = totalSiswa - totalHadir;
                
            } catch (error) {
                console.error('Error loading recent attendance:', error);
            }
        }
        
        // Auto scan functionality
        let autoScanInterval;
        let isScanning = false;
        
        async function autoScan() {
            if (isScanning) return;
            
            isScanning = true;
            const result = await scanQRCode();
            isScanning = false;
            
            if (result.success) {
                // Reload recent attendance setelah scan berhasil
                setTimeout(loadRecentAttendance, 1000);
            }
        }
        
        // Start auto-scan every 2 seconds
        function startAutoScan() {
            autoScanInterval = setInterval(autoScan, 2000);
        }
        
        // Stop auto-scan
        function stopAutoScan() {
            clearInterval(autoScanInterval);
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            updateClock();
            setInterval(updateClock, 1000);
            
            loadRecentAttendance();
            setInterval(loadRecentAttendance, 30000); // Reload every 30 seconds
            
            // Start auto-scan after 3 seconds
            setTimeout(startAutoScan, 3000);
            
            // Manual scan button
            document.getElementById('scan-btn').addEventListener('click', async function() {
                const btn = this;
                const btnText = document.getElementById('btn-text');
                const loading = document.getElementById('btn-loading');
                
                btn.disabled = true;
                btnText.style.display = 'none';
                loading.style.display = 'inline-block';
                
                await autoScan();
                
                btn.disabled = false;
                btnText.style.display = 'inline';
                loading.style.display = 'none';
            });
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            stopAutoScan();
        });
    </script>
</body>
</html>
```

### **B. JavaScript Scanner (`static/js/scanner.js`)**
```javascript
// Scanner functionality
async function scanQRCode() {
    const resultContainer = document.getElementById('result-container');
    const resultTitle = document.getElementById('result-title');
    const resultMessage = document.getElementById('result-message');
    const studentInfo = document.getElementById('student-info');
    
    try {
        // Kirim request scan ke server
        const response = await fetch('/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const data = await response.json();
        
        // Tampilkan hasil
        resultContainer.style.display = 'block';
        
        if (data.success) {
            resultContainer.className = 'result-container result-success';
            resultTitle.textContent = '✅ Absensi Berhasil!';
            resultMessage.textContent = data.message;
            
            // Tampilkan info siswa
            if (data.data) {
                studentInfo.innerHTML = `
                    <div class="info-row">
                        <span class="info-label">Nama:</span>
                        <span class="info-value">${data.data.nama}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Kelas:</span>
                        <span class="info-value">${data.data.kelas}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Waktu:</span>
                        <span class="info-value">${data.data.waktu}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Status:</span>
                        <span class="info-value">
                            <span class="status-badge ${data.data.status === 'Masuk' ? 'status-masuk' : 'status-pulang'}">
                                ${data.data.status}
                            </span>
                        </span>
                    </div>
                `;
            }
            
            // Auto hide setelah 5 detik
            setTimeout(() => {
                resultContainer.style.display = 'none';
            }, 5000);
            
        } else {
            resultContainer.className = 'result-container result-error';
            resultTitle.textContent = '❌ Gagal!';
            resultMessage.textContent = data.message;
            studentInfo.innerHTML = '';
            
            // Auto hide setelah 3 detik
            setTimeout(() => {
                resultContainer.style.display = 'none';
            }, 3000);
        }
        
        return data;
        
    } catch (error) {
        console.error('Scan error:', error);
        
        resultContainer.style.display = 'block';
        resultContainer.className = 'result-container result-error';
        resultTitle.textContent = '❌ Error!';
        resultMessage.textContent = 'Terjadi kesalahan saat scanning';
        studentInfo.innerHTML = '';
        
        setTimeout(() => {
            resultContainer.style.display = 'none';
        }, 3000);
        
        return { success: false, message: 'Error scanning' };
    }
}

// Play sound feedback
function playBeep(type) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = type === 'success' ? 800 : 400;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}
```

## **4. KONFIGURASI APACHE2**

### **A. File WSGI (`absensi.wsgi`)**
```python
import sys
import logging
sys.path.insert(0, '/var/www/absensi')

from absensi_app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()
```

### **B. Virtual Host Apache (`/etc/apache2/sites-available/absensi.conf`)**
```apache
<VirtualHost *:80>
    ServerName localhost
    ServerAdmin admin@sekolah.local
    
    # WSGI Configuration
    WSGIDaemonProcess absensi python-home=/var/www/absensi/venv python-path=/var/www/absensi
    WSGIScriptAlias / /var/www/absensi/absensi.wsgi
    
    <Directory /var/www/absensi>
        WSGIProcessGroup absensi
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    # Static files
    Alias /static /var/www/absensi/static
    <Directory /var/www/absensi/static>
        Require all granted
    </Directory>
    
    # Custom logs
    ErrorLog ${APACHE_LOG_DIR}/absensi_error.log
    CustomLog ${APACHE_LOG_DIR}/absensi_access.log combined
    
    # Security headers
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
```

### **C. Aktifkan Konfigurasi**
```bash
# Disable default site
sudo a2dissite 000-default.conf

# Enable absensi site
sudo a2ensite absensi.conf

# Enable mod_wsgi
sudo a2enmod wsgi

# Restart Apache
sudo systemctl restart apache2
```

## **5. KONFIGURASI AUTO-START CHROMIUM**

### **A. Buat Script Autostart**
```bash
# Buat direktori autostart jika belum ada
mkdir -p ~/.config/autostart

# Buat file desktop autostart
nano ~/.config/autostart/absensi.desktop
```

### **B. Isi File Desktop**
```ini
[Desktop Entry]
Type=Application
Name=Absensi Siswa
Comment=Aplikasi Absensi QR Code
Exec=/usr/bin/chromium-browser --noerrdialogs --disable-infobars --disable-session-crashed-bubble --disable-features=TranslateUI --kiosk http://localhost/
Icon=application-default-icon
X-GNOME-Autostart-enabled=true
Hidden=false
```

### **C. Konfigurasi LightDM (Auto Login)**
```bash
# Edit lightdm configuration
sudo nano /etc/lightdm/lightdm.conf
```

Tambahkan/modifikasi:
```ini
[Seat:*]
autologin-user=pi
autologin-user-timeout=0
```

### **D. Disable Screen Blanking**
```bash
# Edit LXDE autostart
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```

Tambahkan di akhir file:
```
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.1 -root
```

## **6. SCRIPT SETUP OTOMATIS**

### **A. Setup Script (`setup_absensi.sh`)**
```bash
#!/bin/bash
# setup_absensi.sh

echo "=== SETUP APLIKASI ABSENSI SISWA ==="

# Update system
echo "[1/8] Updating system..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "[2/8] Installing dependencies..."
sudo apt install -y \
    apache2 \
    libapache2-mod-wsgi-py3 \
    python3-pip \
    python3-venv \
    chromium-browser \
    unclutter \
    git \
    zbar-tools \
    python3-opencv \
    libcamera-dev

# Clone atau copy aplikasi
echo "[3/8] Setting up application directory..."
sudo mkdir -p /var/www/absensi
sudo chown -R pi:pi /var/www/absensi
cd /var/www/absensi

# Setup virtual environment
echo "[4/8] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "[5/8] Installing Python packages..."
pip install --upgrade pip
pip install \
    flask \
    flask-sqlalchemy \
    flask-cors \
    opencv-python-headless \
    pyzbar \
    pillow \
    numpy \
    pandas

# Setup Apache configuration
echo "[6/8] Configuring Apache..."
sudo cp /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/000-default.conf.backup
sudo tee /etc/apache2/sites-available/absensi.conf > /dev/null <<'EOF'
<VirtualHost *:80>
    ServerName localhost
    WSGIDaemonProcess absensi python-home=/var/www/absensi/venv python-path=/var/www/absensi
    WSGIScriptAlias / /var/www/absensi/absensi.wsgi
    <Directory /var/www/absensi>
        WSGIProcessGroup absensi
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    Alias /static /var/www/absensi/static
    <Directory /var/www/absensi/static>
        Require all granted
    </Directory>
</VirtualHost>
EOF

# Enable site
sudo a2dissite 000-default.conf
sudo a2ensite absensi.conf
sudo a2enmod wsgi
sudo systemctl restart apache2

# Setup autostart
echo "[7/8] Setting up autostart..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/absensi.desktop << EOF
[Desktop Entry]
Type=Application
Name=Absensi Siswa
Exec=/usr/bin/chromium-browser --kiosk --incognito http://localhost/
EOF

# Disable screen blanking
sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart > /dev/null << EOF
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.1 -root
EOF

# Configure auto login
sudo sed -i 's/^#autologin-user=.*/autologin-user=pi/' /etc/lightdm/lightdm.conf
sudo sed -i 's/^#autologin-user-timeout=.*/autologin-user-timeout=0/' /etc/lightdm/lightdm.conf

echo "[8/8] Setup completed!"
echo ""
echo "=== INFORMASI ==="
echo "1. Aplikasi dapat diakses di: http://localhost"
echo "2. Direktori aplikasi: /var/www/absensi"
echo "3. Log Apache: /var/log/apache2/absensi_*.log"
echo "4. Restart Raspberry Pi untuk mengaktifkan auto-start"
echo ""
echo "Untuk menambah data siswa, buat script di: /var/www/absensi/add_students.py"
```

### **B. Script Tambah Siswa (`add_students.py`)**
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/var/www/absensi')

from absensi_app import create_app, db
from absensi_app.models import Siswa
import json

app = create_app()

with app.app_context():
    # Contoh data siswa
    students = [
        {"nis": "2024001", "nama": "ADI SANTOSO", "kelas": "X IPA 1"},
        {"nis": "2024002", "nama": "BUDI RAHARJO", "kelas": "X IPA 1"},
        {"nis": "2024003", "nama": "CITRA DEWI", "kelas": "X IPA 1"},
        {"nis": "2024004", "nama": "DWI PUTRI", "kelas": "X IPA 2"},
        {"nis": "2024005", "nama": "ERWIN WIBOWO", "kelas": "X IPA 2"},
    ]
    
    for student_data in students:
        # Generate QR code data
        qr_data = json.dumps({
            "nis": student_data["nis"],
            "nama": student_data["nama"]
        })
        
        student = Siswa(
            nis=student_data["nis"],
            nama=student_data["nama"],
            kelas=student_data["kelas"],
            qr_code=qr_data
        )
        
        db.session.add(student)
    
    db.session.commit()
    print(f"Added {len(students)} students to database")
    
    # Print QR code data untuk dicetak
    print("\nQR Code Data untuk dicetak:")
    print("="*50)
    for student in Siswa.query.all():
        print(f"NIS: {student.nis}")
        print(f"Nama: {student.nama}")
        print(f"Kelas: {student.kelas}")
        print(f"QR Data: {student.qr_code}")
        print("-"*30)
```

## **7. TESTING & TROUBLESHOOTING**

### **A. Test Camera**
```bash
# Test camera dengan fswebcam
sudo apt install fswebcam
fswebcam test.jpg

# Atau dengan libcamera
libcamera-hello --list-cameras
libcamera-jpeg -o test.jpg
```

### **B. Test Scanner**
```bash
# Test QR code scanner
echo '{"nis":"TEST001"}' | qrencode -o test.png
zbarimg test.png
```

### **C. Monitor Logs**
```bash
# Monitor Apache logs
sudo tail -f /var/log/apache2/absensi_error.log

# Monitor application logs
sudo journalctl -f -u apache2

# Check service status
sudo systemctl status apache2
```

## **8. FITUR TAMBAHAN**

### **A. Backup Database Otomatis**
```bash
# Buat script backup
sudo nano /usr/local/bin/backup_absensi.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/var/www/absensi/absensi.db"

mkdir -p $BACKUP_DIR
cp $DB_PATH "$BACKUP_DIR/absensi_$DATE.db"

# Hapus backup lebih dari 7 hari
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "Backup completed: absensi_$DATE.db"
```

### **B. Sync ke Server Pusat**
```python
# sync_data.py
import requests
import sqlite3
from datetime import datetime

def sync_to_server():
    conn = sqlite3.connect('/var/www/absensi/absensi.db')
    cursor = conn.cursor()
    
    # Get unsynced data
    cursor.execute("SELECT * FROM absensi WHERE synced = 0")
    records = cursor.fetchall()
    
    for record in records:
        try:
            # Send to central server
            response = requests.post(
                'https://server-pusat.example.com/api/absensi',
                json=record,
                timeout=10
            )
            
            if response.status_code == 200:
                # Mark as synced
                cursor.execute(
                    "UPDATE absensi SET synced = 1 WHERE id = ?",
                    (record[0],)
                )
                conn.commit()
        except Exception as e:
            print(f"Sync error: {e}")
    
    conn.close()
```

## **KESIMPULAN**

Dengan setup ini, Raspberry Pi Anda akan:

1. **Auto-start saat dinyalakan** langsung ke aplikasi absensi
2. **Tampilan web fullscreen/kiosk mode** menggunakan Chromium
3. **Backend Flask** yang dihosting dengan Apache2 + mod_wsgi
4. **Scanner QR Code otomatis** dengan kamera USB
5. **Database lokal** (SQLite) untuk operasi offline
6. **UI responsif** dengan auto-scan setiap 2 detik
7. **Monitoring real-time** absensi terbaru

**Untuk deploy:**
1. Jalankan `chmod +x setup_absensi.sh`
2. Jalankan `./setup_absensi.sh`
3. Reboot Raspberry Pi
4. Sistem siap digunakan!

Fleksibel untuk dikembangkan lebih lanjut dengan fitur seperti:
- Face recognition
- RFID/NFC support
- Export laporan Excel
- Notifikasi WhatsApp
- Dashboard admin lengkap
