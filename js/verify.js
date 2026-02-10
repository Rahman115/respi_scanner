async function verifyQR() {
    const textarea = document.getElementById('qrData');
    const result = document.getElementById('result');

    let qrPayload;

    try {
        qrPayload = JSON.parse(textarea.value);
    } catch (e) {
        result.textContent = 'Format QR tidak valid';
        result.style.color = 'red';
        return;
    }

    result.textContent = 'Memverifikasi...';

    try {
        const response = await fetch('http://localhost:8080/api/qr/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                qr_data: qrPayload
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            result.textContent = data.message || 'Verifikasi gagal';
            result.style.color = 'red';
            return;
        }

        result.textContent =
            `VALID\nNama: ${data.student.nama}\nKelas: ${data.student.kelas}`;
        result.style.color = 'green';

    } catch (err) {
        result.textContent = 'Server tidak merespon';
        result.style.color = 'red';
        console.error(err);
    }
}
