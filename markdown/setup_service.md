# SETUP SERVICE
## Membuat service File
```bash
# Buat service file
sudo nano /etc/systemd/system/absensi.service

```
```ini

[Unit]
Description=Sistem Absensi Siswa Flask
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/absensi
Environment="PATH=/opt/absensi/venv/bin"
ExecStart=/opt/absensi/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Aktifkan Service
```bash
# Aktifkan service
sudo systemctl daemon-reload
sudo systemctl enable absensi.service
sudo systemctl start absensi.service
sudo systemctl status absensi.service
```
