const API_URL = "http://localhost:8080/api";

async function generateQR() {
    const nis = document.getElementById('nis').value;
    const status = document.getElementById('status');
    const qrImage = document.getElementById('qrImage');

    if (!nis) {
        status.textContent = 'NIS wajib diisi';
        return;
    }

    status.textContent = 'Mengambil QR...';
    qrImage.src = '';

    try {
        const response = await fetch(`${API_URL}/qr/generate/${nis}`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('token')
            }
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            status.textContent = data.message || 'Gagal generate QR';
            return;
        }

        qrImage.src = data.qr_image;
        status.textContent = 'QR berhasil dibuat';

    } catch (error) {
        status.textContent = 'Server tidak merespon';
        console.error(error);
    }
}
