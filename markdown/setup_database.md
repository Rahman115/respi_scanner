# Dokumentasi Query Database

Dokumentasi ini berisi kumpulan query SQL yang digunakan dalam sistem,
beserta hasil output dan penjelasan singkatnya.

## Struktur Tabel
- Tabel Absensi
- Tabel Siswa
- Tabel Jurusan
- Tabel Kelas
- Tabel Guru
- Tabel Users

## 1. Tabel Absensi

### 1.1 Deskripsi
Tabel `absensi` berfungsi untuk menyimpan seluruh riwayat kehadiran siswa. Setiap baris dalam tabel ini merepresentasikan satu kali proses absensi, baik yang dilakukan melalui mesin scanner maupun input manual.

Tabel ini memiliki relasi many-to-one dengan tabel `siswa`, di mana satu siswa dapat memiliki banyak catatan absensi. Relasi ini diimplementasikan melalui kolom `siswa_id` yang merujuk pada primary key di tabel `siswa`.

### 1.2 Struktur Tabel
Berikut adalah perintah DDL (`CREATE TABLE`) untuk membuat tabel `absensi`.

```sql
CREATE TABLE `absensi` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `siswa_id` int(11) DEFAULT NULL,
  `nis` varchar(20) DEFAULT NULL,
  `tanggal` date NOT NULL,
  `waktu` time NOT NULL,
  `status` enum('hadir','izin','sakit','alpha') DEFAULT 'hadir',
  `metode` enum('scanner','manual') DEFAULT 'scanner',
  `scanner_lokasi` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `siswa_id` (`siswa_id`),
  KEY `idx_tanggal` (`tanggal`),
  KEY `idx_nis` (`nis`),
  CONSTRAINT `absensi_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

### 1.3 Struktur Kolom
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `int(11)` | Primary key, identifikasi unik untuk setiap catatan absensi. Otomatis bertambah. |
| `siswa_id` | `int(11)` | ID siswa dari tabel `siswa` yang melakukan absensi. Bisa `NULL` jika referensi siswa terhapus. |
| `nis` | `varchar(20)` | Nomor Induk Siswa. Kolom ini didenormalisasi untuk mempercepat pencarian tanpa JOIN. |
| `tanggal` | `date` | Tanggal terjadinya absensi. |
| `waktu` | `time` | Waktu terjadinya absensi. |
| `status` | `enum` | Status kehadiran, dengan nilai default 'hadir'. Pilihan: `hadir`, `izin`, `sakit`, `alpha`. |
| `metode` | `enum` | Metode pencatatan absensi, dengan nilai default 'scanner'. Pilihan: `scanner`, `manual`. |
| `scanner_lokasi`| `varchar(50)`| Nama atau lokasi scanner yang digunakan (jika `metode` = 'scanner'). Bisa `NULL`. |

### 1.4 Index dan Constraint
-   **PRIMARY KEY (`id`)** : Memastikan setiap baris data unik dan mempercepat pencarian berdasarkan `id`.
-   **FOREIGN KEY (`siswa_id`)**: Menjaga integritas referensial dengan tabel `siswa`. Memastikan bahwa `siswa_id` yang dimasukkan sudah terdaftar di tabel `siswa`.
-   **KEY `siswa_id` (`siswa_id`)** : Index pada kolom `siswa_id` untuk mempercepat operasi `JOIN` dan pencarian data absensi per siswa.
-   **KEY `idx_tanggal` (`tanggal`)** : Index pada kolom `tanggal` untuk mempercepat pembuatan laporan atau pencarian data dalam rentang tanggal tertentu.
-   **KEY `idx_nis` (`nis`)** : Index pada kolom `nis` untuk mempercepat pencarian data absensi berdasarkan NIS tanpa harus melakukan `JOIN` dengan tabel `siswa`.

### 1.5 Contoh Query

**1. Mengambil semua data absensi hari ini:**
```sql
SELECT * FROM absensi WHERE tanggal = CURDATE();
```

**2. Melihat riwayat absensi seorang siswa (berdasarkan NIS) beserta nama lengkapnya:**
```sql
SELECT 
    a.tanggal, 
    a.waktu, 
    a.status, 
    a.metode,
    s.nama,
    s.nis
FROM absensi a
INNER JOIN siswa s ON a.siswa_id = s.id
WHERE s.nis = '626'  -- NIS siswa yang ingin dicari
ORDER BY a.tanggal DESC, a.waktu DESC;
```

**3. Menghitung jumlah kehadiran per siswa pada bulan Februari 2026:**
```sql
SELECT 
    s.nis,
    s.nama,
    COUNT(*) as total_absensi
FROM absensi a
INNER JOIN siswa s ON a.siswa_id = s.id
WHERE a.tanggal BETWEEN '2026-02-01' AND '2026-02-29'
  AND a.status = 'hadir'
GROUP BY s.id, s.nis, s.nama;
```

**4. Melihat data absensi dengan detail siswa dan kelasnya:**
```sql
SELECT 
    a.tanggal,
    a.waktu,
    s.nis,
    s.nama,
    k.nama_kelas,
    j.nama as jurusan,
    a.status,
    a.metode
FROM absensi a
JOIN siswa s ON a.siswa_id = s.id
LEFT JOIN kelas k ON s.kelas_id = k.id
LEFT JOIN jurusan j ON k.jurusan_id = j.id
WHERE a.tanggal = '2026-02-15'
ORDER BY k.nama_kelas, s.nama;
```

### 1.6 Digunakan Pada
Berdasarkan konteks aplikasi absensi pada umumnya, tabel ini digunakan pada modul-modul berikut:

-   **Modul/Página Scanner**: Untuk menyimpan data ketika siswa melakukan scan kartu/QR code di perangkat scanner.
-   **Modul Rekap/Laporan Absensi**: Untuk menampilkan data kehadiran dalam bentuk grafik atau tabel, biasanya dengan filter tanggal, kelas, atau per siswa.
-   **Modul Input Manual**: Untuk menambahkan, mengedit, atau menghapus data absensi secara manual oleh guru atau admin.
-   **Dashboard**: Untuk menampilkan statistik kehadiran hari ini, seperti total siswa hadir, terlambat, dll.
-   **Endpoint API (jika ada)** :
    -   `POST /api/absensi` : Menerima data dari scanner.
    -   `GET /api/absensi` : Mengambil data absensi untuk laporan.
    -   `GET /api/absensi/siswa/{nis}` : Mengambil riwayat absensi per siswa.

    Tentu, berikut adalah kelanjutan dokumentasi untuk tabel `jurusan`, `kelas`, `siswa`, dan `users` dalam format Markdown yang sama.

---

## 2. Tabel Jurusan

### 2.1 Deskripsi
Tabel `jurusan` berfungsi untuk menyimpan data jurusan yang ada di sekolah. Tabel ini merupakan referensi utama untuk pengelompokan kelas dan siswa.

### 2.2 Struktur Tabel
```sql
CREATE TABLE `jurusan` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `kode` varchar(10) NOT NULL,
  `nama` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `kode` (`kode`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

### 2.3 Struktur Kolom
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `int(11)` | Primary key, identifikasi unik untuk setiap jurusan. |
| `kode` | `varchar(10)` | Kode singkat jurusan (contoh: TITL, TKJ). Bersifat unik. |
| `nama` | `varchar(100)` | Nama lengkap jurusan (contoh: Teknik Komputer dan Jaringan). |

### 2.4 Index dan Constraint
- **PRIMARY KEY (`id`)** : Memastikan setiap baris data unik.
- **UNIQUE KEY `kode` (`kode`)** : Mencegah duplikasi kode jurusan dan mempercepat pencarian berdasarkan kode.

### 2.5 Contoh Query

**Melihat semua jurusan beserta jumlah kelasnya:**
```sql
SELECT 
    j.kode,
    j.nama,
    COUNT(k.id) as jumlah_kelas
FROM jurusan j
LEFT JOIN kelas k ON j.id = k.jurusan_id
GROUP BY j.id, j.kode, j.nama;
```

**Mencari jurusan berdasarkan kode:**
```sql
SELECT * FROM jurusan WHERE kode = 'TKJ';
```

### 2.6 Digunakan Pada
- **Modul Manajemen Jurusan**: Untuk menambah, mengedit, atau menghapus data jurusan.
- **Dropdown Form**: Sebagai pilihan saat menambah atau mengedit data kelas.
- **Laporan Akademik**: Untuk mengelompokkan data berdasarkan jurusan.

---

## 3. Tabel Kelas

### 3.1 Deskripsi
Tabel `kelas` berfungsi untuk menyimpan data kelas/rombongan belajar. Tabel ini berelasi dengan tabel `jurusan` untuk menentukan jurusan dari suatu kelas.

### 3.2 Struktur Tabel
```sql
CREATE TABLE `kelas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `jurusan_id` int(11) NOT NULL,
  `tingkat` enum('1','2','3') NOT NULL,
  `nama_kelas` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `jurusan_id` (`jurusan_id`),
  CONSTRAINT `kelas_ibfk_1` FOREIGN KEY (`jurusan_id`) REFERENCES `jurusan` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

### 3.3 Struktur Kolom
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `int(11)` | Primary key, identifikasi unik untuk setiap kelas. |
| `jurusan_id` | `int(11)` | ID jurusan dari tabel `jurusan` yang menjadi induk kelas ini. |
| `tingkat` | `enum` | Tingkat/kelas, dengan pilihan: '1' (X), '2' (XI), '3' (XII). |
| `nama_kelas` | `varchar(50)` | Nama lengkap kelas (contoh: X TKJ, XI AK). |

### 3.4 Index dan Constraint
- **PRIMARY KEY (`id`)** : Memastikan setiap baris data unik.
- **FOREIGN KEY (`jurusan_id`)**: Menjaga integritas referensial dengan tabel `jurusan`. Dengan opsi `ON DELETE CASCADE`, jika sebuah jurusan dihapus, semua kelas yang terkait akan ikut terhapus.
- **KEY `jurusan_id` (`jurusan_id`)** : Index pada kolom `jurusan_id` untuk mempercepat operasi `JOIN` dengan tabel `jurusan`.

### 3.5 Contoh Query

**Melihat daftar kelas lengkap dengan informasi jurusan:**
```sql
SELECT 
    k.id,
    k.nama_kelas,
    k.tingkat,
    j.kode as kode_jurusan,
    j.nama as nama_jurusan
FROM kelas k
INNER JOIN jurusan j ON k.jurusan_id = j.id
ORDER BY k.tingkat, j.kode;
```

**Menghitung jumlah siswa per kelas:**
```sql
SELECT 
    k.nama_kelas,
    COUNT(s.id) as jumlah_siswa
FROM kelas k
LEFT JOIN siswa s ON k.id = s.kelas_id
GROUP BY k.id, k.nama_kelas
ORDER BY k.nama_kelas;
```

### 3.6 Digunakan Pada
- **Modul Manajemen Kelas**: Untuk menambah, mengedit, atau menghapus data kelas.
- **Dropdown Form Siswa**: Sebagai pilihan saat menambah atau mengedit data siswa.
- **Filter Laporan**: Untuk menyaring data absensi berdasarkan kelas tertentu.

---

## 4. Tabel Siswa

### 4.1 Deskripsi
Tabel `siswa` berfungsi untuk menyimpan data master siswa. Tabel ini merupakan referensi utama untuk tabel `absensi` dan berelasi dengan tabel `kelas`.

### 4.2 Struktur Tabel
```sql
CREATE TABLE `siswa` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nis` varchar(20) NOT NULL,
  `nisn` varchar(10) DEFAULT NULL,
  `nama` varchar(100) NOT NULL,
  `kelas` varchar(20) NOT NULL,
  `qrcode` varchar(64) DEFAULT NULL,
  `tanggal_daftar` timestamp NULL DEFAULT current_timestamp(),
  `card_version` int(11) DEFAULT 1,
  `kelas_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nis` (`nis`),
  UNIQUE KEY `nisn` (`nisn`),
  UNIQUE KEY `qrcode` (`qrcode`),
  KEY `kelas_id` (`kelas_id`),
  CONSTRAINT `siswa_ibfk_1` FOREIGN KEY (`kelas_id`) REFERENCES `kelas` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

### 4.3 Struktur Kolom
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `int(11)` | Primary key, identifikasi unik untuk setiap siswa. |
| `nis` | `varchar(20)` | Nomor Induk Siswa. Bersifat unik dan wajib diisi. |
| `nisn` | `varchar(10)` | Nomor Induk Siswa Nasional. Bersifat unik (dapat NULL). |
| `nama` | `varchar(100)` | Nama lengkap siswa. |
| `kelas` | `varchar(20)` | Kolom lama untuk menyimpan nama kelas (kemungkinan sebelum ada relasi ke tabel `kelas`). |
| `qrcode` | `varchar(64)` | Kode unik untuk QR code siswa. Bersifat unik (dapat NULL). |
| `tanggal_daftar` | `timestamp` | Tanggal dan waktu pendaftaran siswa. Default: waktu sekarang. |
| `card_version` | `int(11)` | Versi kartu siswa, untuk keperluan rotasi/update kartu. Default: 1. |
| `kelas_id` | `int(11)` | ID kelas dari tabel `kelas` tempat siswa terdaftar. Dapat NULL jika kelas dihapus. |

### 4.4 Index dan Constraint
- **PRIMARY KEY (`id`)** : Memastikan setiap baris data unik.
- **UNIQUE KEY `nis` (`nis`)** : Mencegah duplikasi NIS.
- **UNIQUE KEY `nisn` (`nisn`)** : Mencegah duplikasi NISN.
- **UNIQUE KEY `qrcode` (`qrcode`)** : Mencegah duplikasi kode QR.
- **FOREIGN KEY (`kelas_id`)**: Menjaga integritas referensial dengan tabel `kelas`. Dengan opsi `ON DELETE SET NULL`, jika sebuah kelas dihapus, kolom `kelas_id` pada siswa akan diisi NULL.
- **KEY `kelas_id` (`kelas_id`)** : Index pada kolom `kelas_id` untuk mempercepat operasi `JOIN` dengan tabel `kelas`.

### 4.5 Contoh Query

**Melihat data siswa lengkap dengan informasi kelas dan jurusan:**
```sql
SELECT 
    s.nis,
    s.nisn,
    s.nama,
    k.nama_kelas,
    j.nama as jurusan,
    s.tanggal_daftar,
    s.card_version
FROM siswa s
LEFT JOIN kelas k ON s.kelas_id = k.id
LEFT JOIN jurusan j ON k.jurusan_id = j.id
ORDER BY k.nama_kelas, s.nama;
```

**Mencari siswa berdasarkan NIS:**
```sql
SELECT * FROM siswa WHERE nis = '626';
```

**Menghitung jumlah siswa per tingkatan kelas:**
```sql
SELECT 
    k.tingkat,
    CASE 
        WHEN k.tingkat = '1' THEN 'Kelas X'
        WHEN k.tingkat = '2' THEN 'Kelas XI'
        WHEN k.tingkat = '3' THEN 'Kelas XII'
    END as tingkat_nama,
    COUNT(s.id) as jumlah_siswa
FROM siswa s
INNER JOIN kelas k ON s.kelas_id = k.id
GROUP BY k.tingkat
ORDER BY k.tingkat;
```

### 4.6 Digunakan Pada
- **Modul Manajemen Siswa**: Untuk menambah, mengedit, atau menghapus data siswa.
- **Generate QR Code**: Untuk membuat dan mencetak QR code siswa.
- **Modul Absensi**: Sebagai referensi data saat menampilkan riwayat absensi per siswa.
- **Dashboard**: Untuk menampilkan statistik jumlah siswa.

---

## 5. Tabel Users

### 5.1 Deskripsi
Tabel `users` berfungsi untuk menyimpan data pengguna aplikasi, seperti administrator, guru, atau siswa yang memiliki akses ke sistem.

### 5.2 Struktur Tabel
```sql
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `nama` varchar(100) NOT NULL,
  `role` enum('admin','guru','siswa') DEFAULT 'siswa',
  `create_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

### 5.3 Struktur Kolom
| Nama Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `int(11)` | Primary key, identifikasi unik untuk setiap pengguna. |
| `username` | `varchar(50)` | Username untuk login. Bersifat unik. |
| `password` | `varchar(255)` | Password yang sudah di-hash (contoh: MD5). |
| `nama` | `varchar(100)` | Nama lengkap pengguna. |
| `role` | `enum` | Hak akses pengguna, dengan nilai default 'siswa'. Pilihan: `admin`, `guru`, `siswa`. |
| `create_at` | `timestamp` | Tanggal dan waktu pembuatan akun. Default: waktu sekarang. |

### 5.4 Index dan Constraint
- **PRIMARY KEY (`id`)** : Memastikan setiap baris data unik.
- **UNIQUE KEY `username` (`username`)** : Mencegah duplikasi username dan mempercepat proses login.

### 5.5 Contoh Query

**Validasi login pengguna:**
```sql
SELECT * FROM users 
WHERE username = 'admin' 
AND password = '0192023a7bbd73250516f069df18b500'; -- password: admin123 (contoh hash MD5)
```

**Melihat semua pengguna dengan role-nya:**
```sql
SELECT id, username, nama, role, create_at FROM users ORDER BY role, nama;
```

### 5.6 Digunakan Pada
- **Modul Login/Autentikasi**: Untuk memvalidasi kredensial pengguna.
- **Modul Manajemen Pengguna**: Untuk menambah pengguna baru atau mengubah hak akses.
- **Middleware/Otorisasi**: Untuk membatasi akses ke halaman atau fitur tertentu berdasarkan `role` pengguna.
- **Profil Pengguna**: Untuk menampilkan informasi pengguna yang sedang login.