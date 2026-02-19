# Struktur Awal Project (Bertahap, Bukan Langsung Pindah)

Dokumen ini menjelaskan bahwa struktur baru **tidak dipakai dengan cara memindahkan semua file sekaligus**.
Pendekatan yang dipakai adalah migrasi bertahap agar aplikasi lama tetap berjalan.

## Prinsip Implementasi
- ✅ Buat scaffold dulu (sudah dilakukan).
- ✅ Mapping file lama ke lokasi target.
- ⛔ Jangan pindahkan semua file lama sekaligus.
- ✅ Pindah per modul + uji setiap tahap.

## Mapping Folder Lama → Folder Baru

| Folder Lama | Tujuan di Struktur Baru | Catatan |
|---|---|---|
| `absensi/` | `src/frontend/pages/absensi/` | Pindah per halaman (`scan`, `manual`, dst) |
| `siswa/` | `src/frontend/pages/siswa/` | Halaman siswa dipindah bertahap |
| `css/` | `src/frontend/assets/css/` | Konsolidasi stylesheet |
| `js/` | `src/frontend/assets/js/` | Konsolidasi script frontend |
| `includes/` | `src/backend/php/includes/` | Template/header/footer PHP |
| `config/` | `src/backend/php/config/` | Konfigurasi database PHP |
| `api/*.py` | `src/backend/python_api/app/` | Modul Flask/Python API |
| SQL dump/schema | `database/schema.sql` + `database/migrations/` | Mulai versioning schema |

## Rencana Migrasi Bertahap

### Tahap 0 — Stabilkan baseline (sekarang)
- Pastikan aplikasi lama tetap berjalan dengan path lama.
- Gunakan scaffold baru sebagai target, bukan sebagai path aktif.

### Tahap 1 — Frontend assets
- Copy `css/` → `src/frontend/assets/css/`.
- Copy `js/` → `src/frontend/assets/js/`.
- Uji halaman utama + login.

### Tahap 2 — Halaman per modul
- Migrasi `absensi/` dan `siswa/` per file.
- Untuk menghindari break, gunakan adaptor (mis. include/redirect sementara) bila perlu.

### Tahap 3 — Backend PHP & Python API
- Rapikan `config/` dan `includes/` ke `src/backend/php/`.
- Rapikan endpoint Python dari `api/` ke `src/backend/python_api/app/`.
- Validasi endpoint API setelah perpindahan.

## Kriteria Selesai per Tahap
- Tidak ada 404 untuk path yang digunakan pengguna.
- Login, scan, dan absensi manual tetap berfungsi.
- Tidak ada perubahan perilaku tanpa persetujuan.

## Catatan Penting
Scaffold ini adalah **pondasi**. Implementasi real dilakukan step-by-step agar aman di environment produksi/sekolah.
