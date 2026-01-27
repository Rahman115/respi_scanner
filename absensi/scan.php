<!-- /var/www/html/absensi/scan.php -->
<?php
session_start();
require_once '../config/database.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: ../login.php');
    exit();
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scan Absensi</title>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <style>
        .scanner-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
        }
        
        #qr-reader {
            width: 100%;
            max-width: 500px;
            margin: 20px auto;
            border: 2px solid #3498db;
            border-radius: 8px;
            overflow: hidden;
        }
        
        #result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            min-height: 100px;
        }
        
        .success {
            color: #27ae60;
            font-weight: bold;
        }
        
        .error {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .student-info {
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .manual-input {
            margin-top: 30px;
            padding: 20px;
            background: #f1f8ff;
            border-radius: 8px;
        }
        
        .manual-input input {
            padding: 10px;
            font-size: 16px;
            width: 300px;
            margin-right: 10px;
        }
        
        .manual-input button {
            padding: 10px 20px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <?php include '../includes/header.php'; ?>
    
    <div class="content">
        <div class="scanner-container">
            <h1>📷 Scan Absensi Siswa</h1>
            <p>Arahkan kamera ke QR Code / Barcode siswa</p>
            
            <div id="qr-reader"></div>
            
            <div id="result">
                <h3>Hasil Scan:</h3>
                <p id="result-text">Scan barcode siswa untuk memulai</p>
                <div id="student-info" class="student-info" style="display: none;">
                    <h4>✅ Absensi Berhasil</h4>
                    <p><strong>Nama:</strong> <span id="student-name"></span></p>
                    <p><strong>Kelas:</strong> <span id="student-class"></span></p>
                    <p><strong>Waktu:</strong> <span id="scan-time"></span></p>
                </div>
            </div>
            
            <div class="manual-input">
                <h3>Atau Input Manual</h3>
                <input type="text" id="manual-nis" placeholder="Masukkan NIS siswa">
                <button onclick="processManualScan()">Submit</button>
            </div>
            
            <div style="margin-top: 30px;">
                <a href="manual.php" style="padding: 10px 20px; background: #95a5a6; color: white; text-decoration: none; border-radius: 4px;">
                    ⌨️ Ke Input Manual
                </a>
                <a href="../index.php" style="padding: 10px 20px; background: #7f8c8d; color: white; text-decoration: none; border-radius: 4px; margin-left: 10px;">
                    ← Kembali ke Dashboard
                </a>
            </div>
        </div>
    </div>
    
    <script>
    // HTML5 QR Code Scanner
    const html5QrCode = new Html5Qrcode("qr-reader");
    
    // Konfigurasi scanner
    const qrCodeConfig = {
        fps: 10,
        qrbox: 250,
        disableFlip: false
    };
    
    // Mulai scanner
    html5QrCode.start(
        { facingMode: "environment" },
        qrCodeConfig,
        onScanSuccess
    ).catch(err => {
        console.error("Scanner error:", err);
        document.getElementById('result-text').innerHTML = 
            '<span class="error">Error: Kamera tidak dapat diakses. Pastikan izin kamera diberikan.</span>';
    });
    
    // Fungsi ketika scan berhasil
    function onScanSuccess(decodedText) {
        console.log("Scan result:", decodedText);
        
        // Tampilkan loading
        document.getElementById('result-text').innerHTML = 
            '<span>Memproses scan...</span>';
        
        // Kirim ke API
        processScan(decodedText);
    }
    
    // Fungsi proses scan
    async function processScan(nis) {
        try {
            const response = await fetch('http://localhost:5000/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ nis: nis })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Tampilkan success
                document.getElementById('result-text').innerHTML = 
                    '<span class="success">✅ Scan berhasil diproses!</span>';
                
                // Tampilkan info siswa
                document.getElementById('student-name').textContent = result.siswa.nama;
                document.getElementById('student-class').textContent = result.siswa.kelas;
                document.getElementById('scan-time').textContent = result.siswa.waktu;
                document.getElementById('student-info').style.display = 'block';
                
                // Play success sound
                playBeep();
                
                // Reset setelah 3 detik
                setTimeout(() => {
                    document.getElementById('student-info').style.display = 'none';
                    document.getElementById('result-text').textContent = 'Scan barcode siswa untuk memulai';
                }, 3000);
                
            } else {
                document.getElementById('result-text').innerHTML = 
                    `<span class="error">❌ ${result.message}</span>`;
                playErrorBeep();
            }
            
        } catch (error) {
            console.error("API error:", error);
            document.getElementById('result-text').innerHTML = 
                '<span class="error">❌ Error koneksi ke server</span>';
            playErrorBeep();
        }
    }
    
    // Fungsi untuk input manual
    function processManualScan() {
        const nis = document.getElementById('manual-nis').value.trim();
        
        if (!nis) {
            alert('Masukkan NIS siswa');
            return;
        }
        
        processScan(nis);
        document.getElementById('manual-nis').value = '';
    }
    
    // Sound effects
    function playBeep() {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }
    
    function playErrorBeep() {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 300;
        oscillator.type = 'sawtooth';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 1);
    }
    
    // Keyboard shortcut untuk input manual
    document.getElementById('manual-nis').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            processManualScan();
        }
    });
    </script>
    
    <?php include '../includes/footer.php'; ?>
</body>
</html>
