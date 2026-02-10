#!/bin/bash
# Setup script for Absensi API

echo "=== SETUP ABSENSI API ==="

# 1. Generate QR Secret
echo "1. Generating QR secret key..."
QR_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "QR_SECRET_KEY=$QR_SECRET"

# 2. Generate JWT Secret
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "JWT_SECRET_KEY=$JWT_SECRET"

# 3. Update service file
echo "2. Updating systemd service..."
sudo sed -i "s|QR_SECRET_KEY=.*|QR_SECRET_KEY=$QR_SECRET|" /etc/systemd/system/scanner-api.service
sudo sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" /etc/systemd/system/scanner-api.service

# 4. Update config file
echo "3. Updating config file..."
sudo sed -i "s|QR_SECRET_KEY = .*|QR_SECRET_KEY = '$QR_SECRET'|" /var/www/html/api/config.py
sudo sed -i "s|JWT_SECRET_KEY = .*|JWT_SECRET_KEY = '$JWT_SECRET'|" /var/www/html/api/config.py

# 5. Set permissions
echo "4. Setting permissions..."
sudo chown -R pi:www-data /var/www/html/api
sudo chmod -R 755 /var/www/html/api
sudo chmod +x /var/www/html/api/api.py

# 6. Create log directory
echo "5. Creating log directory..."
sudo mkdir -p /var/www/html/api/logs
sudo chown pi:www-data /var/www/html/api/logs
sudo chmod 775 /var/www/html/api/logs

# 7. Reload systemd
echo "6. Reloading systemd..."
sudo systemctl daemon-reload

echo "=== SETUP COMPLETE ==="
echo ""
echo "To start the API:"
echo "  sudo systemctl start scanner-api"
echo "  sudo systemctl enable scanner-api"
echo ""
echo "To check status:"
echo "  sudo systemctl status scanner-api"
echo "  sudo journalctl -u scanner-api -f"
