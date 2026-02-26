# utils/json_encoder.py
"""
Custom JSON Encoder untuk menangani serialisasi objek datetime, date, time, dan timedelta
"""

import json
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from flask.json.provider import JSONProvider

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder yang bisa handle objek datetime, date, time, timedelta"""
    
    def default(self, obj):
        # Handle date objects
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # Handle time objects
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        
        # Handle timedelta objects (selisih waktu)
        if isinstance(obj, timedelta):
            total_seconds = int(obj.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
         # Handle Decimal objects (dari MySQL)
        if isinstance(obj, Decimal):
            return float(obj)
        
        # Handle other types
        return super().default(obj)


class CustomJSONProvider(JSONProvider):
    """Custom JSON Provider untuk Flask 3.x"""
    
    def __init__(self, app):
        super().__init__(app)
    
    def dumps(self, obj, **kwargs):
        """Convert obj to JSON string using custom encoder"""
        return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)
    
    def loads(self, s, **kwargs):
        """Convert JSON string to Python object"""
        return json.loads(s, **kwargs)


# Fungsi utilitas untuk mengkonversi objek ke JSON string
def to_json_string(obj, **kwargs):
    """Convert object to JSON string using custom encoder"""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)


# Fungsi untuk setup JSON provider di Flask app
def setup_json_provider(app):
    """Setup custom JSON provider untuk Flask app"""
    
    # Untuk Flask 3.x
    try:
        app.json = CustomJSONProvider(app)
        return True
    except:
        pass
    
    # Untuk Flask < 2.2 (fallback)
    try:
        app.json_encoder = CustomJSONEncoder
        return True
    except:
        return False
