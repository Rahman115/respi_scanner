Saya akan membantu Anda menguji coba fungsi masing-masing endpoint dari API Absensi ini. Berikut adalah panduan pengujian lengkap untuk semua blueprint:

## 1. **System & Health Check**
```bash
# Cek status API
curl -X GET http://localhost:5000/

# Cek health system
curl -X GET http://localhost:5000/api/system/health

# Test endpoint legacy
curl -X GET http://localhost:5000/api/test
```

## 2. **Authentication**
```bash
# Login (sesuaikan dengan kredensial yang ada)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

simpan token 
```bash 
TOKEN="code_token"
# dantuliskan seperti ini
curl -X GET http://localhost:5000/api/students   
-H "Authorization: Bearer $TOKEN"

```

## 3. **Students (Siswa)**
```bash
# Get all students
curl -X GET http://localhost:5000/api/students

# Get student by NIS
curl -X GET http://localhost:5000/api/students/12345

# Get students by kelas
curl -X GET http://localhost:5000/api/students/by-kelas/1

# Get statistics by class
curl -X GET http://localhost:5000/api/students/statistics/by-kelas

# Check NISN
curl -X GET "http://localhost:5000/api/students/check-nisn?nisn=1234567890"

# Add new student
curl -X POST http://localhost:5000/api/students/add \
  -H "Content-Type: application/json" \
  -d '{
    "nis": "12345",
    "nisn": "1234567890",
    "nama_siswa": "Budi Santoso",
    "kelas_id": 1,
    "jenis_kelamin": "L",
    "tempat_lahir": "Jakarta",
    "tanggal_lahir": "2005-01-15",
    "alamat": "Jl. Merdeka No. 10",
    "no_telp": "08123456789"
  }'

# Update student
curl -X PUT http://localhost:5000/api/students/12345 \
  -H "Content-Type: application/json" \
  -d '{
    "nama_siswa": "Budi Santoso Update",
    "alamat": "Jl. Baru No. 20"
  }'

# Delete student
curl -X DELETE http://localhost:5000/api/students/12345
```

## 4. **Teachers (Guru)**
```bash
# Get all teachers
curl -X GET http://localhost:5000/api/guru

# Get teacher by ID
curl -X GET http://localhost:5000/api/guru/1

# Get teacher by NIP
curl -X GET http://localhost:5000/api/guru/nip/198001012010011001

# Search teachers
curl -X GET "http://localhost:5000/api/guru/search?q=ahmad"

# Get teachers with kelas
curl -X GET http://localhost:5000/api/guru/with-kelas

# Get statistics
curl -X GET http://localhost:5000/api/guru/statistics

# Add new teacher
curl -X POST http://localhost:5000/api/guru \
  -H "Content-Type: application/json" \
  -d '{
    "nip": "198001012010011001",
    "nama_guru": "Ahmad Fauzi",
    "jenis_kelamin": "L",
    "tempat_lahir": "Bandung",
    "tanggal_lahir": "1980-01-01",
    "pendidikan": "S1",
    "bidang_studi": "Matematika",
    "no_telp": "081234567890",
    "alamat": "Jl. Pendidikan No. 5",
    "status": "aktif"
  }'

# Update teacher
curl -X PUT http://localhost:5000/api/guru/1 \
  -H "Content-Type: application/json" \
  -d '{
    "nama_guru": "Ahmad Fauzi, S.Pd",
    "bidang_studi": "Matematika Lanjutan"
  }'

# Delete teacher
curl -X DELETE http://localhost:5000/api/guru/1
```

## 5. **Classes (Kelas)**
```bash
# Get all classes
curl -X GET http://localhost:5000/api/kelas

# Get class by ID
curl -X GET http://localhost:5000/api/kelas/1

# Get classes by jurusan
curl -X GET http://localhost:5000/api/kelas/by-jurusan/1

# Get classes by tingkat
curl -X GET http://localhost:5000/api/kelas/by-tingkat/10

# Get classes by wali kelas
curl -X GET http://localhost:5000/api/kelas/wali-kelas/1

# Get statistics
curl -X GET http://localhost:5000/api/kelas/statistics

# Get students in class
curl -X GET http://localhost:5000/api/kelas/1/siswa

# Add new class
curl -X POST http://localhost:5000/api/kelas \
  -H "Content-Type: application/json" \
  -d '{
    "nama_kelas": "XII RPL 1",
    "tingkat": 12,
    "jurusan_id": 1,
    "wali_kelas_id": 5,
    "tahun_ajaran": "2024/2025"
  }'

# Update class
curl -X PUT http://localhost:5000/api/kelas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "nama_kelas": "XII RPL 1 - Unggulan",
    "kapasitas": 36
  }'

# Delete class
curl -X DELETE http://localhost:5000/api/kelas/1
```

## 6. **Attendance (Absensi)**
```bash
# Get today's attendance
curl -X GET http://localhost:5000/api/attendance/today

# Get attendance by date
curl -X GET "http://localhost:5000/api/attendance/by-date?date=2026-05-19"

# Get student attendance history
curl -X GET http://localhost:5000/api/attendance/student/12345

# Get statistics
curl -X GET "http://localhost:5000/api/attendance/statistics?start_date=2026-01-01&end_date=2026-12-31"

# Get summary by class
curl -X GET http://localhost:5000/api/attendance/summary/by-class

# Manual attendance
curl -X POST http://localhost:5000/api/attendance/manual \
  -H "Content-Type: application/json" \
  -d '{
    "nis": "12345",
    "status": "hadir",
    "keterangan": "Tepat waktu",
    "tanggal": "2026-05-19"
  }'

# Update attendance
curl -X PUT http://localhost:5000/api/attendance/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "sakit",
    "keterangan": "Izin sakit"
  }'

# Delete attendance
curl -X DELETE http://localhost:5000/api/attendance/1
```

## 7. **QR Code**
```bash
# Generate QR code for student
curl -X GET http://localhost:5000/api/qr/generate/12345

# Bulk generate QR codes
curl -X POST http://localhost:5000/api/qr/bulk/generate \
  -H "Content-Type: application/json" \
  -d '{
    "kelas_id": 1,
    "nis_list": ["12345", "12346", "12347"]
  }'

# Verify QR code
curl -X POST http://localhost:5000/api/qr/verify \
  -H "Content-Type: application/json" \
  -d '{
    "qr_data": "QR_CODE_DATA_HERE"
  }'

# Get QR history
curl -X GET http://localhost:5000/api/qr/history/12345

# Print QR code
curl -X GET http://localhost:5000/api/qr/print/12345

# Validate NISN
curl -X POST http://localhost:5000/api/qr/validate-nisn \
  -H "Content-Type: application/json" \
  -d '{
    "nisn": "1234567890",
    "nama_siswa": "Budi Santoso"
  }'
```

## 8. **Scanner**
```bash
# Scan by NIS
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "nis": "12345"
  }'

# Scan by NISN
curl -X POST http://localhost:5000/api/scan-nisn \
  -H "Content-Type: application/json" \
  -d '{
    "nisn": "1234567890"
  }'

# Check scan status
curl -X GET http://localhost:5000/api/scan-status/12345

# Get scan history
curl -X GET "http://localhost:5000/api/scan-history?limit=50"
```

## 9. **Debug**
```bash
# Get table structure
curl -X GET http://localhost:5000/api/debug/table-structure

# Create backup
curl -X POST http://localhost:5000/api/debug/backup \
  -H "Content-Type: application/json" \
  -d '{
    "backup_name": "backup_20260519"
  }'

# List backups
curl -X GET http://localhost:5000/api/debug/backups

# Restore backup
curl -X POST http://localhost:5000/api/debug/restore \
  -H "Content-Type: application/json" \
  -d '{
    "backup_file": "backup_20260519.sql"
  }'

# Get logs
curl -X GET "http://localhost:5000/api/debug/logs?lines=100"

# Performance check
curl -X GET http://localhost:5000/api/debug/performance

# Fix NISN issues
curl -X POST http://localhost:5000/api/debug/fix-nisn \
  -H "Content-Type: application/json" \
  -d '{
    "dry_run": true
  }'

# Cleanup
curl -X POST http://localhost:5000/api/debug/cleanup \
  -H "Content-Type: application/json" \
  -d '{
    "clean_old_qr": true,
    "clean_old_logs": true,
    "days_old": 30
  }'
```

## Tips Pengujian:

1. **Uji Berurutan**: Mulai dari endpoint yang paling sederhana (system/health) baru ke yang kompleks

2. **Simpan Token Auth**: Jika auth sudah diimplementasikan, simpan token untuk request berikutnya:
   ```bash
   # Simpan token
   TOKEN="your_token_here"
   
   # Gunakan token
   curl -X GET http://localhost:5000/api/students \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **Cek Response Format**: Pastikan semua response memiliki format konsisten:
   ```json
   {
     "success": true,
     "data": {...},
     "message": "...",
     "timestamp": "..."
   }
   ```

4. **Error Handling**: Uji juga skenario error (data tidak ditemukan, input invalid, dll)

5. **Performance**: Catat response time untuk masing-masing endpoint

Apakah Anda ingin saya membantu menguji blueprint tertentu terlebih dahulu, atau ada kendala saat mencoba salah satu endpoint di atas?
