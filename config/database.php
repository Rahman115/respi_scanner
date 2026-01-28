<!-- /var/www/html/config/database.php -->
<?php
$host = 'localhost';
$user = 'root';
$pass = 'admin';
$dbname = 'absensi_siswa';

$conn = mysqli_connect($host, $user, $pass, $dbname);

if (!$conn) {
    die("Koneksi database gagal: " . mysqli_connect_error());
}

mysqli_set_charset($conn, "utf8");
?>
