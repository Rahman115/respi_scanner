<!-- /var/www/html/config/database.php -->
<?php
$host = 'localhost';
$user = 'absensi_user';
$pass = 'pass123';
$dbname = 'absensi_siswa';

$conn = mysqli_connect($host, $user, $pass, $dbname);

if (!$conn) {
    die("Koneksi database gagal: " . mysqli_connect_error());
}

mysqli_set_charset($conn, "utf8");
?>
