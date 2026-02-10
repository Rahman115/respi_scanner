<!-- /var/www/html/index.php -->
<?php
session_start();

include "config/database.php";

// Redirect jika belum login
if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit();
}

// Ambil statistik
$today = date('Y-m-d');


$query_total = mysqli_query($conn, "SELECT COUNT(*) as total FROM siswa");
$query_hadir = mysqli_query($conn, "SELECT COUNT(DISTINCT siswa_id) as hadir FROM absensi WHERE tanggal = '$today' AND status = 'Hadir'");

$total = mysqli_fetch_assoc($query_total)['total'];
$hadir = mysqli_fetch_assoc($query_hadir)['hadir'];
$tidak_hadir = $total - $hadir;



// Ambil absensi hari ini
$query_absensi = mysqli_query($conn, "
    SELECT a.*, s.nama, s.kelas
    FROM absensi a
    JOIN siswa s ON a.siswa_id = s.id
    WHERE a.tanggal = '$today'
    ORDER BY a.waktu DESC
    LIMIT 10
");


?>

<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Sistem Absensi</title>
</head>
<body>
    <?php include 'includes/header.php'; ?>

    <div class="content">
        <h1>SMKN 4 Buton Utara</h1>
        <p>Dashboard Sistem Absensi Siswa [ login : <?php echo $_SESSION['nama']; ?>]</p>

        <!-- Stats Cards -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0;">
            <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; text-align: center;">
                <h3>Total Siswa</h3>
                <p style="font-size: 2rem; font-weight: bold; color: #1976d2;"><?php echo $total; ?></p>
            </div>

            <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; text-align: center;">
                <h3>Hadir Hari Ini</h3>
                <p style="font-size: 2rem; font-weight: bold; color: #388e3c;"><?php echo $hadir; ?></p>
            </div>

            <div style="background: #ffebee; padding: 20px; border-radius: 8px; text-align: center;">
                <h3>Tidak Hadir</h3>
                <p style="font-size: 2rem; font-weight: bold; color: #d32f2f;"><?php echo $tidak_hadir; ?></p>
            </div>

            <div style="background: #fff3e0; padding: 20px; border-radius: 8px; text-align: center;">
                <h3>Persentase</h3>
                <p style="font-size: 2rem; font-weight: bold; color: #f57c00;">
                    <?php echo $total > 0 ? round(($hadir/$total)*100, 1) : 0; ?>%
                </p>
            </div>
        </div>

        <!-- Quick Actions -->
        <div style="display: flex; gap: 15px; margin: 30px 0;">
            <a href="absensi/scan.php" style="padding: 15px 25px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">
                📷 Scan Absensi
            </a>
            <a href="absensi/manual.php" style="padding: 15px 25px; background: #2ecc71; color: white; text-decoration: none; border-radius: 5px;">
                ⌨️ Input Manual
            </a>
            <a href="siswa/index.html" style="padding: 15px 25px; background: #9b59b6; color: white; text-decoration: none; border-radius: 5px;">
                👥 Data Siswa
            </a>
            <a href="laporan/harian.php" style="padding: 15px 25px; background: #e67e22; color: white; text-decoration: none; border-radius: 5px;">
                📊 Laporan
            </a>
        </div>

        <!-- Recent Absensi -->
        <h2>Absensi Hari Ini</h2>
        <?php if (mysqli_num_rows($query_absensi) > 0): ?>
        <table>
            <thead>
                <tr>
                    <th>Waktu</th>
                    <th>NIS</th>
                    <th>Nama</th>
                    <th>Kelas</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <?php while ($row = mysqli_fetch_assoc($query_absensi)): ?>
                <tr>
                    <td><?php echo $row['waktu']; ?></td>
                    <td><?php echo $row['nis']; ?></td>
                    <td><?php echo $row['nama']; ?></td>
                    <td><?php echo $row['kelas']; ?></td>
                    <td>
                        <span style="padding: 5px 10px; border-radius: 3px;
                              background: <?php echo $row['status'] == 'Hadir' ? '#d4edda' :
                                          ($row['status'] == 'Izin' ? '#fff3cd' :
                                          ($row['status'] == 'Sakit' ? '#d1ecf1' : '#f8d7da')); ?>;">
                            <?php echo $row['status']; ?>
                        </span>
                    </td>
                </tr>
                <?php endwhile; ?>
            </tbody>
        </table>
        <?php else: ?>
        <p>Belum ada absensi hari ini.</p>
        <?php endif; ?>
    </div>

    <?php include 'includes/footer.php'; ?>
</body>
</html>
