# Rencana Migrasi ke MVC (Bertahap)

Ya, migrasi bisa dilakukan dengan pola **MVC** dan sebaiknya bertahap agar fitur lama tidak rusak.

## Target Struktur MVC (PHP)

```text
src/backend/php/
├── public/
│   └── index.php
└── app/
    ├── Core/
    │   ├── App.php
    │   └── Router.php
    ├── Controllers/
    │   ├── BaseController.php
    │   ├── AuthController.php
    │   └── DashboardController.php
    ├── Models/
    │   └── BaseModel.php
    └── Views/
        ├── layouts/main.php
        ├── auth/login.php
        └── dashboard/index.php
```

## Mapping Fitur Lama → MVC

| Lama | MVC Baru |
|---|---|
| `login.html` | `AuthController::showLogin()` + `Views/auth/login.php` |
| `index.html` | `DashboardController::index()` + `Views/dashboard/index.php` |
| `absensi/manual.php` | `AttendanceController::manual()` + `AttendanceModel` + `Views/attendance/manual.php` |
| `absensi/scan.php` | `AttendanceController::scan()` + `Views/attendance/scan.php` |
| `config/database.php` | dipakai sementara oleh `BaseModel` |

## Tahapan Implementasi

1. **Scaffold MVC aktif**: front controller + router + controller/view dasar.
2. **Migrasi auth**: pindah login ke controller + view, path lama tetap diberi fallback.
3. **Migrasi dashboard**: pindah render dashboard ke view MVC.
4. **Migrasi absensi**: pecah query dari `manual.php`/`scan.php` ke model.
5. **Cleanup**: hapus fallback lama setelah semua route stabil.

## Cara Menjalankan (mode MVC percobaan)

```bash
php -S localhost:8001 -t src/backend/php/public
```

Lalu buka:
- `http://localhost:8001/`
- `http://localhost:8001/login`

## Catatan
- Implementasi ini scaffold awal, belum menggantikan aplikasi lama.
- Endpoint Python API tetap bisa digunakan paralel selama masa migrasi.
