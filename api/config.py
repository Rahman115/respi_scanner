"""
Konfigurasi untuk Absensi API
"""

import os
from datetime import timedelta

#QR Code secret key
QR_SECRET_KEY = '91925a3ed95ca6e5ce31b7bf5e56c926d9b19d65ae4e43b493d4aca985f53476'

#JWT Configuration
JWT_SECRET_KEY = 'mv99FIpXr4Sj3s2DP6M92OjpAQs_qVzGEMSU9KBwWzY'
JWT_ACCESS_TOKEN_EXPIRE = timedelta(hours=1)

# Database Configuration
DB_CONFIG = {
	'host': 'localhost',
	'user': 'absensi_user',
	'password': 'pass123',
	'database': 'absensi_siswa'
}

# Scanner Configuration
SCANNER_CONFIG = {
	'default_location': 'Gerbang Utama',
	'max_attempts': 3,
	'timeout_seconds': 5
}

# QR Code Configuration
QR_CONFIG = {
	'version': 1,
	'box_size': 10,
	'border': 4,
	'error_correction': 'H' #H : High error corection
}

# API Configuration
API_CONFIG = {
	'host': '0.0.0.0',
	'port': 8080, #app.run(port=8080) / test 5000
	'debug': False,
	'threaded': True
}
