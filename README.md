# APLIKASI ABSENSI SISWA
### Update Version 3.04

Aplikasi absensi siswa berbasis web dengan fitur manual dan scan QR code untuk pencatatan kehadiran.

## 🚀 FITUR UTAMA
- Absensi manual melalui form input
- Absensi otomatis via scan QR code
- API untuk integrasi dengan scanner eksternal
- Antarmuka responsif dan mudah digunakan
- Sistem login untuk keamanan data

## 📁 STRUKTUR PROYEK
```text

absensi/
├── manual.php          # Halaman absensi manual
├── scan.php            # Halaman scan QR code
config/
├── database.php        # Konfigurasi koneksi database
includes/
├── header.php          # Template header
├── footer.php          # Template footer
js/
├── script.js           # File JavaScript
css/                   # File stylesheet
├── style.css
api/
├── api.py              # API Python untuk scanner
├── get_activity.php    # Endpoint get aktivitas
├── scanner-api.py      # API utama scanner QR
├── venv/               # Virtual environment Python
siswa/                  # Halaman terkait data siswa
index.html              # Halaman utama/dashboard
login.html              # Halaman login
README.md               # Dokumentasi ini
```

## ⚙️ PERSYARATAN SISTEM

### Server Web
- PHP 7.4 atau lebih baru
- Apache/Nginx web server
- MySQL 5.7+ / MariaDB 10.2+

### Python (untuk API scanner)
- Python 3.8 atau lebih baru
- pip (Python package manager)

### Ekstensi PHP yang Diperlukan
- PDO MySQL
- JSON
- cURL (jika menggunakan API eksternal)

## 📦 INSTALASI

### 1. Clone/Download Proyek
```bash
git clone [url-repository]
cd absensi-siswa
```

### 2. Setup Database
```sql
-- Buat database
CREATE DATABASE absensi_siswa;

-- Import struktur database (jika ada file .sql)
-- mysql -u username -p absensi_siswa < database.sql
```

### 3. Konfigurasi Database
Edit file `config/database.php`:
```php
<?php
$host = 'localhost';
$dbname = '';
$username = '';
$password = '';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    die("Koneksi database gagal: " . $e->getMessage());
}
?>
```

### 4. Setup Python API (Opsional)
Jika menggunakan fitur scanner QR via Python:

```bash
cd api

# Buat virtual environment (jika belum ada)
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install flask flask-cors pillow qrcode
```

### 5. Konfigurasi Web Server
- Copy semua file ke directory web server (htdocs/www)
- Pastikan folder memiliki permission yang tepat:
```bash
chmod 755 -R /path/to/absensi
```

### 6. Identifikasi dan hentikan proses yang menggunakan port 8080
```bash
# Cari PID proses yang menggunakan port 8080
sudo lsof -i :8080

sudo netstat -tulpn | grep :8080 # alternaif lain

# Hentikan proses tersebut
sudo kill -9 <PID>
sleep 2 # tunggu beberapa saat

# Verifikasi port sudah kosong
sudo lsof -i :8080

# Jalankan ulang API Anda
python3 api.py


```



## 🏃 CARA MENJALANKAN

### 1. Start Web Server
- Aktifkan Apache/MySQL melalui XAMPP/MAMP/WAMP
- Atau gunakan PHP built-in server:
```bash
php -S localhost:8000
```

### 2. Start Python API (jika digunakan)
```bash
cd api
# Aktifkan virtual environment terlebih dahulu
python scanner-api.py
```
API akan berjalan di `http://localhost:5000`

### 3. Akses Aplikasi
- Buka browser
- Kunjungi: `http://localhost/[folder-proyek]`
- Login dengan kredensial yang telah dibuat

## 🔧 KONFIGURASI TAMBAHAN

### 1. Timezone
Tambahkan di `index.php` atau buat file `config/timezone.php`:
```php
date_default_timezone_set('Asia/Jakarta');
```

### 2. Session Configuration
Pastikan session sudah dimulai di file utama:
```php
session_start();
```

### 3. Security
- Ubah default password database
- Gunakan HTTPS untuk produksi
- Update credential login default

## 📝 PENGGUNAAN

### Absensi Manual
1. Akses `/absensi/manual.php`
2. Pilih/pilih nama siswa
3. Pilih status kehadiran
4. Submit data

### Absensi Scan QR
1. Akses `/absensi/scan.php`
2. Arahkan kamera ke QR code siswa
3. Data akan otomatis terekam

### API Endpoints
- `GET /api/get_activity.php` - Mendapatkan data aktivitas
- `POST /api/scanner-api.py/scan` - Endpoint scan QR code

## 🐛 TROUBLESHOOTING

### Masalah Koneksi Database
- Periksa kredensial di `config/database.php`
- Pastikan MySQL service berjalan
- Cek firewall jika koneksi remote

### API Python Tidak Berjalan
- Pastikan Python terinstall
- Aktifkan virtual environment
- Install semua dependency

### QR Code Tidak Terbaca
- Pastikan kamera mendukung
- Cek permission akses kamera di browser
- Verifikasi lighting/pencahayaan

### Menghapus File Logs
```bash
sudo truncate -s 0 /var/www/html/api/logs/api.log

```


## 📄 LISENSI
Proyek ini dikembangkan untuk keperluan internal sekolah.

## 🤝 KONTRIBUSI
Untuk saran atau perbaikan, silakan buat issue atau pull request.

## 📞 KONTAK
Untuk pertanyaan lebih lanjut, hubungi pengembang aplikasi.

---
*Dokumentasi terakhir diperbarui: 2026 februari 04*

## 🧱 STRUKTUR AWAL (SCAFFOLD)
- Rencana migrasi ke pola MVC tersedia di `docs/MIGRASI_MVC.md` dan dijalankan bertahap.
- Struktur awal baru telah disiapkan di `src/`, `database/`, `scripts/`, dan `docs/STRUKTUR_AWAL.md`.
- Implementasi dilakukan **bertahap** (bukan pindah massal) dengan mapping folder lama→baru agar aplikasi tetap stabil.
- Detail rencana ada di `docs/STRUKTUR_AWAL.md`.

