<?php
// /var/www/html/api/get_activity.php 
// (untuk web monitor)
// API untuk mendapatkan aktivitas terbaru

header('Content-Type: application/json');
require_once '../config/database.php';

$today = date('Y-m-d');

// Get recent activity
$query = "
    SELECT a.*, s.nama, s.kelas 
    FROM absensi a 
    JOIN siswa s ON a.siswa_id = s.id 
    WHERE a.tanggal = '$today' 
    ORDER BY a.waktu DESC 
    LIMIT 20
";

$result = mysqli_query($conn, $query);

$activity = [];
while ($row = mysqli_fetch_assoc($result)) {
    $activity[] = [
        'nis' => $row['nis'],
        'nama' => $row['nama'],
        'kelas' => $row['kelas'],
        'waktu' => $row['waktu'],
        'status' => $row['status'],
        'location' => $row['scanner_lokasi'] ?: 'manual'
    ];
}

// Get scanner statistics
$stats_query = "
    SELECT 
        COALESCE(scanner_lokasi, 'manual') as location,
        COUNT(*) as count,
        MAX(waktu) as last_scan
    FROM absensi 
    WHERE tanggal = '$today'
    GROUP BY scanner_lokasi
";

$stats_result = mysqli_query($conn, $stats_query);
$scanners = [];

$i = 1;
while ($stat = mysqli_fetch_assoc($stats_result)) {
    $scanners[] = [
        'id' => $i,
        'name' => "Scanner $i - " . $stat['location'],
        'location' => $stat['location'],
        'count' => $stat['count'],
        'last_scan' => $stat['last_scan']
    ];
    $i++;
}

echo json_encode([
    'success' => true,
    'activity' => $activity,
    'scanners' => $scanners
]);
?>