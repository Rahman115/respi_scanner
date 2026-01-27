<!-- /var/www/html/includes/header.php -->
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistem Absensi Siswa</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; line-height: 1.6; background: #f4f4f4; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: #2c3e50; color: white; padding: 15px 0; }
        nav { display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.5rem; font-weight: bold; }
        .nav-links { display: flex; list-style: none; }
        .nav-links li { margin-left: 20px; }
        .nav-links a { color: white; text-decoration: none; padding: 5px 10px; }
        .nav-links a:hover { background: #34495e; }
        .content { background: white; padding: 20px; margin-top: 20px; border-radius: 5px; }
        .btn { padding: 10px 20px; background: #3498db; color: white; border: none; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f2f2f2; }
        .alert { padding: 15px; margin: 10px 0; border-radius: 4px; }
        .alert-success { background: #d4edda; color: #155724; }
        .alert-error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <nav>
                <div class="logo">📚 Absensi Siswa</div>
                <ul class="nav-links">
                    <li><a href="/">Dashboard</a></li>
                    <li><a href="/absensi/">Absensi</a></li>
                    <li><a href="/siswa/">Data Siswa</a></li>
                    <li><a href="/laporan/">Laporan</a></li>
                    <?php if(isset($_SESSION['user_id'])): ?>
                        <li><a href="/logout.php">Logout</a></li>
                    <?php endif; ?>
                </ul>
            </nav>
        </div>
    </header>
    <div class="container">
