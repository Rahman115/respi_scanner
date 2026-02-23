# utils/database.py
import mysql.connector
from mysql.connector import Error
import logging
from config import DB_CONFIG

logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def fetch_one(query, params=None):
    """Fetch one row"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchone()
    except Error as e:
        logger.error(f"Query error: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def fetch_all(query, params=None):
    """Fetch all rows"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Query error: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def execute(query, params=None, commit=False):
    """Execute query (INSERT, UPDATE, DELETE)"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return {'success': False, 'error': 'Connection failed'}
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        result = {'success': True}
        if commit:
            conn.commit()
            result['rowcount'] = cursor.rowcount
            result['last_id'] = cursor.lastrowid
        
        return result
    except Error as e:
        logger.error(f"Execute error: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
