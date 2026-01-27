<!-- /var/www/html/absensi/manual.php -->
<?php
session_start();
require_once '../config/database.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: ../login.php');
    exit();
}

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $nis = mysqli_real_escape_string($conn, $_POST['nis']);
    $status = mysqli_real_escape_string($conn, $_POST['status']);
    
    // Cari siswa
    $query = "SELECT * FROM siswa WHERE nis = '$nis'";
    $result = mysqli_query($conn, $query);
    
    if (mysqli_num_rows($result) == 1) {
        $siswa = mysqli_fetch_assoc($result);
        $today = date('Y-m-d');
        $now = date('H:i:s');
        
        // Cek apakah sudah absen
        $check = mysqli_query($conn, 
            "SELECT * FROM absensi WHERE siswa_id = '{$siswa['id']}' AND tanggal = '$today'");
        
        if (mysqli_num_rows($check) == 0) {
            // Simpan absensi
            mysqli_query($conn, 
                "INSERT INTO absensi (siswa_id, nis, tanggal, waktu, status, metode) 
                 VALUES ('{$siswa['id']}', '$nis', '$today', '$now', '$status', 'Manual')");
            
            $success = "Absensi berhasil: {$siswa['nama']} - {$siswa['kelas']}";
        } else {
            $error = "Siswa sudah absen hari ini";
        }
    } else {
        $error = "NIS tidak ditemukan";
    }
}

// Ambil daftar siswa untuk autocomplete
$siswa_list = mysqli_query($conn, "SELECT nis, nama, kelas FROM siswa ORDER BY kelas, nama");
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Input Manual Absensi</title>
    <style>
        .form-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        
        .btn-submit {
            padding: 12px 30px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        
        .btn-submit:hover {
            background: #2980b9;
        }
        
        .autocomplete-list {
            border: 1px solid #ddd;
            max-height: 200px;
            overflow-y: auto;
            display: none;
            position: absolute;
            background: white;
            width: 100%;
            z-index: 1000;
        }
        
        .autocomplete-item {
            padding: 10px;
            cursor: pointer;
        }
        
        .autocomplete-item:hover {
            background: #f0f0f0;
        }
    </style>
</head>
<body>
    <?php include '../includes/header.php'; ?>
    
    <div class="content">
        <div class="form-container">
            <h1>⌨️ Input Manual Absensi</h1>
            
            <?php if (isset($success)): ?>
                <div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                    <?php echo $success; ?>
                </div>
            <?php endif; ?>
            
            <?php if (isset($error)): ?>
                <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                    <?php echo $error; ?>
                </div>
            <?php endif; ?>
            
            <form method="POST" action="">
                <div class="form-group">
                    <label for="nis">NIS Siswa *</label>
                    <input type="text" id="nis" name="nis" required 
                           placeholder="Masukkan NIS atau nama siswa"
                           onkeyup="showSuggestions(this.value)">
                    <div id="suggestions" class="autocomplete-list"></div>
                </div>
                
                <div class="form-group">
                    <label for="status">Status Kehadiran *</label>
                    <select id="status" name="status" required>
                        <option value="Hadir">Hadir</option>
                        <option value="Izin">Izin</option>
                        <option value="Sakit">Sakit</option>
                        <option value="Alpha">Alpha</option>
                    </select>
                </div>
                
                <button type="submit" class="btn-submit">Simpan Absensi</button>
            </form>
            
            <div style="margin-top: 40px;">
                <h3>Daftar Siswa</h3>
                <table>
                    <thead>
                        <tr>
                            <th>NIS</th>
                            <th>Nama</th>
                            <th>Kelas</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php while ($siswa = mysqli_fetch_assoc($siswa_list)): ?>
                        <tr>
                            <td><?php echo $siswa['nis']; ?></td>
                            <td><?php echo $siswa['nama']; ?></td>
                            <td><?php echo $siswa['kelas']; ?></td>
                        </tr>
                        <?php endwhile; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
    // Data siswa untuk autocomplete
    const siswaData = [
        <?php 
        mysqli_data_seek($siswa_list, 0);
        while ($siswa = mysqli_fetch_assoc($siswa_list)): 
        ?>
        {
            nis: "<?php echo $siswa['nis']; ?>",
            nama: "<?php echo $siswa['nama']; ?>",
            kelas: "<?php echo $siswa['kelas']; ?>"
        },
        <?php endwhile; ?>
    ];
    
    // Fungsi untuk menampilkan suggestions
    function showSuggestions(query) {
        const suggestions = document.getElementById('suggestions');
        
        if (query.length < 2) {
            suggestions.style.display = 'none';
            return;
        }
        
        const filtered = siswaData.filter(siswa => 
            siswa.nis.toLowerCase().includes(query.toLowerCase()) ||
            siswa.nama.toLowerCase().includes(query.toLowerCase())
        );
        
        if (filtered.length === 0) {
            suggestions.style.display = 'none';
            return;
        }
        
        let html = '';
        filtered.forEach(siswa => {
            html += `<div class="autocomplete-item" onclick="selectSiswa('${siswa.nis}', '${siswa.nama} - ${siswa.kelas}')">
                        <strong>${siswa.nis}</strong> - ${siswa.nama} (${siswa.kelas})
                     </div>`;
        });
        
        suggestions.innerHTML = html;
        suggestions.style.display = 'block';
    }
    
    // Fungsi untuk memilih siswa
    function selectSiswa(nis, displayText) {
        document.getElementById('nis').value = nis;
        document.getElementById('suggestions').style.display = 'none';
    }
    
    // Tutup suggestions ketika klik di luar
    document.addEventListener('click', function(e) {
        if (e.target.id !== 'nis') {
            document.getElementById('suggestions').style.display = 'none';
        }
    });
    </script>
    
    <?php include '../includes/footer.php'; ?>
</body>
</html>
