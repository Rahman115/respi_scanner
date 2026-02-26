# blueprints/attendance.py
from flask import Blueprint, request, jsonify
from utils.database import fetch_one, fetch_all, execute
from utils.auth import token_required
from datetime import date, datetime, timedelta
import logging

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')
logger = logging.getLogger(__name__)


# ===========================================
# GET TODAY'S ATTENDANCE
# ===========================================
@attendance_bp.route('/today', methods=['GET'])
@token_required
def get_today_attendance():
    """Get today's attendance records"""
    try:
        kelas_id = request.args.get('kelas_id')
        status = request.args.get('status')

        today = date.today()

        query = """
            SELECT 
                a.*,
                s.nama,
                s.nis,
                s.nisn,
                s.gender,
                s.kelas_id,
                k.nama_kelas as kelas
            FROM absensi a
            JOIN siswa s ON a.siswa_id = s.id
            LEFT JOIN kelas k ON s.kelas_id = k.id
            WHERE a.tanggal = %s
        """
        params = [today]

        if kelas_id:
            query += " AND s.kelas_id = %s"
            params.append(kelas_id)

        if status:
            query += " AND a.status = %s"
            params.append(status)

        query += " ORDER BY a.waktu DESC"

        attendance = fetch_all(query, tuple(params))

        # Get total students count for statistics
        total_query = "SELECT COUNT(*) as total FROM siswa"
        total_params = []

        if kelas_id:
            total_query += " WHERE kelas_id = %s"
            total_params.append(kelas_id)

        total_students = fetch_one(total_query, tuple(total_params) if total_params else None)

        return jsonify({
            "success": True,
            "date": str(today),
            "total_students": total_students['total'] if total_students else 0,
            "attended": len(attendance),
            "attendance": attendance
        })

    except Exception as e:
        logger.error(f"Get today attendance error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET ATTENDANCE BY DATE
# ===========================================
@attendance_bp.route('/by-date', methods=['GET'])
@token_required
def get_attendance_by_date():
    """Get attendance records for a specific date"""
    try:
        date_param = request.args.get('date', date.today().isoformat())
        kelas_id = request.args.get('kelas_id')
        status = request.args.get('status')

        try:
            attendance_date = date.fromisoformat(date_param)
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Format tanggal tidak valid. Gunakan YYYY-MM-DD"
            }), 400

        query = """
            SELECT 
                a.*,
                s.nama,
                s.nis,
                s.nisn,
                s.gender,
                s.kelas_id,
                k.nama_kelas as kelas
            FROM absensi a
            JOIN siswa s ON a.siswa_id = s.id
            LEFT JOIN kelas k ON s.kelas_id = k.id
            WHERE a.tanggal = %s
        """
        params = [attendance_date]

        if kelas_id:
            query += " AND s.kelas_id = %s"
            params.append(kelas_id)

        if status:
            query += " AND a.status = %s"
            params.append(status)

        query += " ORDER BY k.nama_kelas, s.nama"

        attendance = fetch_all(query, tuple(params))

        return jsonify({
            "success": True,
            "date": date_param,
            "count": len(attendance),
            "attendance": attendance
        })

    except Exception as e:
        logger.error(f"Get attendance by date error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET ATTENDANCE BY STUDENT
# ===========================================
@attendance_bp.route('/student/<nis>', methods=['GET'])
@token_required
def get_student_attendance(nis):
    """Get attendance history for a specific student"""
    try:
        # Get student info
        student = fetch_one("""
            SELECT id, nis, nisn, nama, gender, kelas_id
            FROM siswa WHERE nis = %s
        """, (nis,))

        if not student:
            return jsonify({
                "success": False,
                "message": f"Siswa dengan NIS {nis} tidak ditemukan"
            }), 404

        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)

        query = """
            SELECT 
                tanggal,
                waktu,
                status,
                metode,
                scanner_lokasi
            FROM absensi
            WHERE siswa_id = %s
        """
        params = [student['id']]

        if start_date:
            query += " AND tanggal >= %s"
            params.append(start_date)

        if end_date:
            query += " AND tanggal <= %s"
            params.append(end_date)

        query += " ORDER BY tanggal DESC, waktu DESC LIMIT %s"
        params.append(limit)

        attendance = fetch_all(query, tuple(params))

        # Get statistics
        stats = fetch_one("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Hadir' THEN 1 END) as hadir,
                COUNT(CASE WHEN status = 'Izin' THEN 1 END) as izin,
                COUNT(CASE WHEN status = 'Sakit' THEN 1 END) as sakit,
                COUNT(CASE WHEN status = 'Alpha' THEN 1 END) as alpha,
                MIN(tanggal) as first_attendance,
                MAX(tanggal) as last_attendance
            FROM absensi
            WHERE siswa_id = %s
        """, (student['id'],))

        return jsonify({
            "success": True,
            "student": student,
            "statistics": {
                "total": stats['total'] or 0,
                "hadir": stats['hadir'] or 0,
                "izin": stats['izin'] or 0,
                "sakit": stats['sakit'] or 0,
                "alpha": stats['alpha'] or 0,
                "first_attendance": str(stats['first_attendance']) if stats['first_attendance'] else None,
                "last_attendance": str(stats['last_attendance']) if stats['last_attendance'] else None
            },
            "attendance": attendance,
            "total_records": len(attendance)
        })

    except Exception as e:
        logger.error(f"Get student attendance error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET ATTENDANCE STATISTICS
# ===========================================
@attendance_bp.route('/statistics', methods=['GET'])
@token_required
def get_attendance_statistics():
    """Get attendance statistics for a date range"""
    try:
        start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
        end_date = request.args.get('end_date', date.today().isoformat())

        # Daily statistics
        daily_stats = fetch_all("""
            SELECT 
                tanggal as date,
                COUNT(DISTINCT siswa_id) as total_siswa,
                COUNT(*) as total_records,
                COUNT(CASE WHEN status = 'Hadir' THEN 1 END) as hadir,
                COUNT(CASE WHEN status = 'Izin' THEN 1 END) as izin,
                COUNT(CASE WHEN status = 'Sakit' THEN 1 END) as sakit,
                COUNT(CASE WHEN status = 'Alpha' THEN 1 END) as alpha
            FROM absensi
            WHERE tanggal BETWEEN %s AND %s
            GROUP BY tanggal
            ORDER BY tanggal DESC
        """, (start_date, end_date))

        # Statistics by class
        class_stats = fetch_all("""
            SELECT 
                k.id as kelas_id,
                k.nama_kelas,
                k.tingkat,
                j.nama as jurusan,
                COUNT(DISTINCT a.siswa_id) as total_siswa_absen,
                COUNT(a.id) as total_absensi,
                COUNT(CASE WHEN a.status = 'Hadir' THEN 1 END) as hadir,
                COUNT(CASE WHEN a.status = 'Izin' THEN 1 END) as izin,
                COUNT(CASE WHEN a.status = 'Sakit' THEN 1 END) as sakit,
                COUNT(CASE WHEN a.status = 'Alpha' THEN 1 END) as alpha,
                (SELECT COUNT(*) FROM siswa WHERE kelas_id = k.id) as total_siswa
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN siswa s ON k.id = s.kelas_id
            LEFT JOIN absensi a ON s.id = a.siswa_id 
                AND a.tanggal BETWEEN %s AND %s
            GROUP BY k.id, k.nama_kelas, k.tingkat, j.nama
            ORDER BY k.tingkat, j.nama, k.nama_kelas
        """, (start_date, end_date))

        # Statistics by status
        status_stats = fetch_all("""
            SELECT 
                status,
                COUNT(*) as total,
                COUNT(DISTINCT siswa_id) as unique_students
            FROM absensi
            WHERE tanggal BETWEEN %s AND %s
            GROUP BY status
            ORDER BY total DESC
        """, (start_date, end_date))

        # Summary
        summary = fetch_one("""
            SELECT 
                COUNT(DISTINCT siswa_id) as total_siswa_absen,
                COUNT(*) as total_absensi,
                COUNT(DISTINCT tanggal) as total_hari
            FROM absensi
            WHERE tanggal BETWEEN %s AND %s
        """, (start_date, end_date))

        return jsonify({
            "success": True,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "total_days": (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1
            },
            "summary": {
                "total_absensi": summary['total_absensi'] if summary else 0,
                "total_siswa_absen": summary['total_siswa_absen'] if summary else 0,
                "total_hari": summary['total_hari'] if summary else 0,
                "rata_rata_harian": round((summary['total_absensi'] or 0) / (summary['total_hari'] or 1), 1)
            },
            "daily_statistics": daily_stats,
            "class_statistics": class_stats,
            "status_statistics": status_stats
        })

    except Exception as e:
        logger.error(f"Get attendance statistics error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET ATTENDANCE SUMMARY BY CLASS
# ===========================================
@attendance_bp.route('/summary/by-class', methods=['GET'])
@token_required
def get_summary_by_class():
    """Get attendance summary grouped by class for a specific date"""
    try:
        date_param = request.args.get('date', date.today().isoformat())

        try:
            attendance_date = date.fromisoformat(date_param)
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Format tanggal tidak valid. Gunakan YYYY-MM-DD"
            }), 400

        summary = fetch_all("""
            SELECT 
                k.id as kelas_id,
                k.nama_kelas,
                k.tingkat,
                j.nama as jurusan,
                COUNT(DISTINCT s.id) as total_siswa,
                COUNT(DISTINCT a.siswa_id) as hadir,
                COUNT(CASE WHEN a.status = 'Izin' THEN 1 END) as izin,
                COUNT(CASE WHEN a.status = 'Sakit' THEN 1 END) as sakit,
                COUNT(CASE WHEN a.status = 'Alpha' THEN 1 END) as alpha,
                (COUNT(DISTINCT s.id) - COUNT(DISTINCT a.siswa_id)) as tidak_hadir
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN siswa s ON k.id = s.kelas_id
            LEFT JOIN absensi a ON s.id = a.siswa_id AND a.tanggal = %s
            GROUP BY k.id, k.nama_kelas, k.tingkat, j.nama
            ORDER BY k.tingkat, j.nama, k.nama_kelas
        """, (attendance_date,))

        # Add percentage
        for item in summary:
            if item['total_siswa'] > 0:
                item['persentase_hadir'] = round((item['hadir'] / item['total_siswa']) * 100, 1)
            else:
                item['persentase_hadir'] = 0

        return jsonify({
            "success": True,
            "date": date_param,
            "total_kelas": len(summary),
            "summary": summary
        })

    except Exception as e:
        logger.error(f"Get summary by class error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# MANUAL ATTENDANCE ENTRY
# ===========================================
@attendance_bp.route('/manual', methods=['POST'])
@token_required
def manual_attendance():
    """Manually add attendance record"""
    try:
        data = request.get_json()

        required_fields = ["nis", "status"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "message": f"{field} harus diisi"
                }), 400

        nis = data['nis'].strip()
        status = data['status']
        tanggal = data.get('tanggal', date.today().isoformat())
        keterangan = data.get('keterangan', '')

        # Validate status
        valid_status = ['Hadir', 'Izin', 'Sakit', 'Alpha', 'Terlambat']
        if status not in valid_status:
            return jsonify({
                "success": False,
                "message": f"Status harus salah satu: {', '.join(valid_status)}"
            }), 400

        # Get student
        student = fetch_one("SELECT id, nis, nama FROM siswa WHERE nis = %s", (nis,))
        if not student:
            return jsonify({
                "success": False,
                "message": f"Siswa dengan NIS {nis} tidak ditemukan"
            }), 404

        # Check if already exists
        existing = fetch_one("""
            SELECT id FROM absensi 
            WHERE siswa_id = %s AND tanggal = %s
        """, (student['id'], tanggal))

        if existing:
            return jsonify({
                "success": False,
                "message": f"{student['nama']} sudah memiliki absensi pada tanggal {tanggal}"
            }), 409

        # Insert attendance
        now = datetime.now()
        result = execute("""
            INSERT INTO absensi
            (siswa_id, nis, tanggal, waktu, status, metode, keterangan)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            student['id'],
            student['nis'],
            tanggal,
            now.time(),
            status,
            'manual',
            keterangan
        ), commit=True)

        if not result['success']:
            return jsonify({
                "success": False,
                "message": "Gagal menyimpan absensi"
            }), 500

        return jsonify({
            "success": True,
            "message": "Absensi berhasil ditambahkan",
            "attendance": {
                "id": result.get('last_id'),
                "nis": student['nis'],
                "nama": student['nama'],
                "tanggal": tanggal,
                "status": status,
                "metode": "manual"
            }
        }), 201

    except Exception as e:
        logger.error(f"Manual attendance error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# UPDATE ATTENDANCE
# ===========================================
@attendance_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_attendance(id):
    """Update attendance record"""
    try:
        data = request.get_json()

        if not data or 'status' not in data:
            return jsonify({
                "success": False,
                "message": "Status harus diisi"
            }), 400

        status = data['status']
        keterangan = data.get('keterangan', '')

        # Validate status
        valid_status = ['Hadir', 'Izin', 'Sakit', 'Alpha', 'Terlambat']
        if status not in valid_status:
            return jsonify({
                "success": False,
                "message": f"Status harus salah satu: {', '.join(valid_status)}"
            }), 400

        # Check if attendance exists
        existing = fetch_one("SELECT id FROM absensi WHERE id = %s", (id,))
        if not existing:
            return jsonify({
                "success": False,
                "message": f"Absensi dengan ID {id} tidak ditemukan"
            }), 404

        # Update
        result = execute("""
            UPDATE absensi 
            SET status = %s, keterangan = %s 
            WHERE id = %s
        """, (status, keterangan, id), commit=True)

        if not result['success']:
            return jsonify({
                "success": False,
                "message": "Gagal mengupdate absensi"
            }), 500

        return jsonify({
            "success": True,
            "message": "Absensi berhasil diupdate",
            "attendance": {
                "id": id,
                "status": status,
                "keterangan": keterangan
            }
        })

    except Exception as e:
        logger.error(f"Update attendance error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# DELETE ATTENDANCE
# ===========================================
@attendance_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_attendance(id):
    """Delete attendance record"""
    try:
        # Check if exists
        existing = fetch_one("SELECT id FROM absensi WHERE id = %s", (id,))
        if not existing:
            return jsonify({
                "success": False,
                "message": f"Absensi dengan ID {id} tidak ditemukan"
            }), 404

        # Delete
        result = execute("DELETE FROM absensi WHERE id = %s", (id,), commit=True)

        if not result['success'] or result.get('rowcount', 0) == 0:
            return jsonify({
                "success": False,
                "message": "Gagal menghapus absensi"
            }), 500

        return jsonify({
            "success": True,
            "message": "Absensi berhasil dihapus"
        })

    except Exception as e:
        logger.error(f"Delete attendance error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
