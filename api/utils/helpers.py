# utils/helpers.py (tambahkan fungsi ini)
import qrcode
import io
import base64
from config import QR_CONFIG

def generate_qr_image(data):
    """Generate QR code image and return as base64"""
    try:
        qr = qrcode.QRCode(
            version=QR_CONFIG["version"],
            error_correction=getattr(
                qrcode.constants, f"ERROR_CORRECT_{QR_CONFIG['error_correction']}"
            ),
            box_size=QR_CONFIG["box_size"],
            border=QR_CONFIG["border"],
        )

        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return base64.b64encode(img_bytes.getvalue()).decode("utf-8")
    except Exception as e:
        logger.error(f"QR generation error: {e}")
        return None

def validate_nisn(nisn):
    """Validate NISN format (10 digits)"""
    if not nisn:
        return False
    nisn_str = str(nisn).strip()
    return len(nisn_str) == 10 and nisn_str.isdigit()
