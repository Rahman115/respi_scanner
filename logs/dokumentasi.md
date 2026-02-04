# Dokumentasi API Absensi Sekolah

## 📋 Ringkasan Proyek

API absensi siswa berbasis REST yang dibangun dengan **Python Flask** dan berjalan di **Raspberry Pi**. Sistem ini memungkinkan pencatatan kehadiran siswa secara real-time menggunakan nomor induk siswa (NIS).

## 🚀 Spesifikasi Teknis

### **Server Information**
- **Framework**: Werkzeug 2.2.2 (Python Flask)
- **Python Version**: 3.11.2
- **Host**: Raspberry Pi
- **Port**: 8080
- **IP Address**: 192.168.1.11

### **Endpoint API**
```
POST http://192.168.1.11:8080/api/scan
```

### **Metode yang Didukung**
- `POST` - Untuk melakukan absensi
- `OPTIONS` - Untuk preflight CORS requests

## 📝 Struktur Request & Response

### **Request Format**
```json
{
  "nis": "2026002"
}
```

### **Response Format (Success)**
```json
{
  "success": true,
  "message": "Absensi berhasil",
  "attendance_id": 5,
  "timestamp": "2026-02-03T05:47:36.553274",
  "student": {
    "id": 2,
    "nis": "2026002",
    "nama": "Alfin",
    "kelas": "XI TKJ"
  },
  "attendance": {
    "date": "2026-02-03",
    "time": "05:47:36",
    "method": "Scanner",
    "status": "Hadir",
    "location": "Unknown"
  }
}
```

### **Response Format (Already Checked In)**
```json
{
  "success": false,
  "message": "Alfin sudah absen hari ini",
  "student": {
    "nis": "2026002",
    "nama": "Alfin",
    "kelas": "XI TKJ"
  },
  "previous_attendance": {
    "method": "scanner",
    "time": "6:35:44"
  }
}
```

## 🔧 Cara Penggunaan

### **1. Menggunakan cURL**
```bash
# Basic request
curl -X POST http://192.168.1.11:8080/api/scan \
  -H "Content-Type: application/json" \
  -d '{"nis": "2026002"}'

# With verbose output
curl -v -X POST http://192.168.1.11:8080/api/scan \
  -H "Content-Type: application/json" \
  -d '{"nis": "2026002"}'
```

### **2. Menggunakan JavaScript (Frontend)**
```javascript
async function scanStudent(nis) {
  try {
    const response = await fetch('http://192.168.1.11:8080/api/scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ nis: nis })
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error:', error);
    return { success: false, message: 'Network error' };
  }
}

// Contoh penggunaan
scanStudent('2026002').then(result => {
  console.log(result);
  if (result.success) {
    alert(`Absensi berhasil untuk ${result.student.nama}`);
  } else {
    alert(result.message);
  }
});
```

### **3. Menggunakan Python**
```python
import requests

def scan_attendance(nis):
    url = "http://192.168.1.11:8080/api/scan"
    payload = {"nis": nis}
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Contoh penggunaan
result = scan_attendance("2026002")
print(result)
```

## ⚠️ Troubleshooting yang Ditemukan

### **Masalah: "Endpoint not found" di Browser**
**Penyebab**: Browser melakukan GET request secara default, sedangkan endpoint hanya menerima POST

**Solusi**:
1. Gunakan HTTP Client seperti Postman atau Insomnia
2. Gunakan JavaScript fetch API dengan method POST
3. Gunakan cURL dari terminal

### **Masalah: CORS Errors**
**Solusi**:
- Tambahkan header Origin jika diperlukan
- Konfigurasi CORS di server Flask

### **Masalah: Port Tidak Responsif**
**Verifikasi koneksi**:
```bash
# Cek apakah server berjalan
curl -X OPTIONS http://192.168.1.11:8080/api/scan

# Cek proses di port 8080
sudo lsof -i :8080

# Restart jika diperlukan
sudo systemctl restart [service-name]
```

## 📊 Contoh Data Siswa yang Terdaftar

| NIS      | Nama   | Kelas    | ID  |
|----------|--------|----------|-----|
| 2026001  | [Nama] | [Kelas]  | 1   |
| 2026002  | Alfin  | XI TKJ   | 2   |
| 2026003  | [Nama] | [Kelas]  | 3   |

## 🎯 Fitur Sistem

1. **Validasi Duplikasi**: Mencegah absensi ganda pada hari yang sama
2. **Struktur Data Lengkap**: Menyimpan informasi siswa dan waktu absensi
3. **Real-time Response**: Response langsung setelah scan
4. **Error Handling**: Pesan error yang informatif
5. **Method Validation**: Hanya menerima POST dan OPTIONS

## 🔒 Keamanan

1. **Input Validation**: Validasi format NIS
2. **Method Restriction**: Hanya metode tertentu yang diizinkan
3. **Data Consistency**: Mencegah data duplikat

## 🚀 Deployment Notes

### **Requirements**
```txt
Flask==2.2.2
Werkzeug==2.2.2
```

### **Run Server**
```bash
# Development mode
python app.py

# Production (contoh)
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## 📈 Monitoring

### **Log Format**
```
192.168.1.11 - - [03/Feb/2026 05:45:27] "OPTIONS /api/scan HTTP/1.1" 200 -
```

### **Health Check**
```bash
# Cek status server
curl -X OPTIONS http://192.168.1.11:8080/api/scan
```

## 📚 Lesson Learned

1. **REST API Design**: Endpoint harus jelas dan konsisten
2. **Error Messages**: Pesan error harus informatif
3. **CORS Handling**: Penting untuk web applications
4. **Input Validation**: Validasi input di client dan server
5. **Documentation**: Dokumentasi yang baik penting untuk maintenance

## 🔮 Pengembangan Selanjutnya

1. [ ] Tambahkan endpoint GET untuk melihat riwayat absensi
2. [ ] Implementasi autentikasi API key
3. [ ] Dashboard admin untuk monitoring
4. [ ] Export data ke Excel/PDF
5. [ ] Notifikasi real-time (WebSocket)

---

**Terakhir Diuji**: 3 Februari 2026  
**Status**: ✅ Berfungsi dengan baik  
**Maintainer**: [Nama Anda]  
**Kontak**: [Email/Telepon]  

---

*Dokumen ini akan diperbarui sesuai perkembangan sistem.*
