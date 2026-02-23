# blueprints/students.py
from flask import Blueprint, request, jsonify
from utils.database import fetch_one, fetch_all, execute
from utils.auth import token_required
import logging

students_bp = Blueprint("students", __name__, url_prefix="/api/students")
logger = logging.getLogger(__name__)


# ===========================================
# GET ALL STUDENTS
# ===========================================
@students_bp.route("", methods=["GET"])
@token_required
def get_students():
    """Get all students with optional filtering by kelas_id"""
    try:
        kelas_id = request.args.get("kelas_id")

        if kelas_id:
            query = """SELECT 
                s.id, s.nis, s.nisn, s.nama, s.gender,
                s.kelas_id, s.card_version,
                k.nama_kelas as kelas, 
                k.tingkat,
                j.nama as jurusan,
                j.kode as jurusan_kode
            FROM siswa s
            LEFT JOIN kelas k ON s.kelas_id = k.id
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            WHERE s.kelas_id = %s 
            ORDER BY s.nama"""
            students = fetch_all(query, (kelas_id,))
        else:
            query = """SELECT 
                s.id, s.nis, s.nisn, s.nama, s.gender,
                s.kelas_id, s.card_version,
                k.nama_kelas as kelas, 
                k.tingkat,
                j.nama as jurusan,
                j.kode as jurusan_kode
            FROM siswa s
            LEFT JOIN kelas k ON s.kelas_id = k.id
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            ORDER BY k.tingkat, j.nama, k.nama_kelas, s.nama"""
            students = fetch_all(query)

        # Add gender labels
        for student in students:
            student["gender_label"] = (
                "Laki-laki"
                if student["gender"] == "L"
                else "Perempuan" if student["gender"] == "P" else "-"
            )

        return jsonify({"success": True, "count": len(students), "students": students})

    except Exception as e:
        logger.error(f"Get students error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET STUDENT DETAIL BY NIS
# ===========================================
@students_bp.route("/<nis>", methods=["GET"])
@token_required
def get_student_detail(nis):
    """Get detailed student information by NIS"""
    try:
        # Get student data with kelas information
        student = fetch_one(
            """
            SELECT 
                s.id, s.nis, s.nisn, s.nama, s.gender,
                s.kelas_id, s.card_version,
                k.nama_kelas as kelas,
                k.tingkat,
                j.nama as jurusan,
                j.kode as jurusan_kode,
                g.nama as wali_kelas_nama
            FROM siswa s
            LEFT JOIN kelas k ON s.kelas_id = k.id
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            WHERE s.nis = %s
        """,
            (nis,),
        )

        if not student:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Siswa dengan NIS {nis} tidak ditemukan",
                    }
                ),
                404,
            )

        # Get attendance statistics
        stats = fetch_one(
            """
            SELECT 
                COUNT(*) as total_attendance,
                COUNT(CASE WHEN status = 'Hadir' THEN 1 END) as hadir,
                COUNT(CASE WHEN status = 'Izin' THEN 1 END) as izin,
                COUNT(CASE WHEN status = 'Sakit' THEN 1 END) as sakit,
                COUNT(CASE WHEN status = 'Alpha' THEN 1 END) as alpha,
                MAX(tanggal) as last_attendance_date
            FROM absensi 
            WHERE siswa_id = %s
        """,
            (student["id"],),
        )

        # Get recent attendance
        recent = fetch_all(
            """
            SELECT tanggal, waktu, status, metode, scanner_lokasi
            FROM absensi 
            WHERE siswa_id = %s 
            ORDER BY tanggal DESC, waktu DESC 
            LIMIT 10
        """,
            (student["id"],),
        )
        
        # Convert waktu from timedelta/time to string for JSON serialization
        formatted_recent = []
        for attendance in recent:
            formatted_attendance = dict(attendance)
            # Convert waktu to string if it's a timedelta or time object
            if attendance["waktu"] is not None:
                # Jika berupa timedelta, konversi ke string HH:MM:SS
                if hasattr(attendance["waktu"], "seconds"):
                    total_seconds = attendance["waktu"].seconds
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    formatted_attendance["waktu"] = (
                        f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    )
                else:
                    # Jika sudah berupa string atau tipe lain, konversi ke string
                    formatted_attendance["waktu"] = str(attendance["waktu"])
            formatted_recent.append(formatted_attendance)
            
        # Check today's attendance
        today_attendance = fetch_one(
            """
            SELECT id FROM absensi 
            WHERE siswa_id = %s AND tanggal = CURDATE()
        """,
            (student["id"],),
        )

        # Format response
        student_data = {
            "id": student["id"],
            "nis": student["nis"] or "",
            "nisn": student["nisn"] or "",
            "nama": student["nama"] or "",
            "gender": student["gender"],
            "gender_label": (
                "Laki-laki"
                if student["gender"] == "L"
                else "Perempuan" if student["gender"] == "P" else "-"
            ),
            "kelas_id": student["kelas_id"],
            "kelas": student["kelas"] or "",
            "tingkat": student["tingkat"] or "",
            "jurusan": student["jurusan"] or "",
            "jurusan_kode": student["jurusan_kode"] or "",
            "wali_kelas_nama": student["wali_kelas_nama"] or "",
            "card_version": student["card_version"] or 1,
        }

        return jsonify(
            {
                "success": True,
                "student": student_data,
                "statistics": {
                    "total_attendance": stats["total_attendance"] or 0,
                    "hadir": stats["hadir"] or 0,
                    "izin": stats["izin"] or 0,
                    "sakit": stats["sakit"] or 0,
                    "alpha": stats["alpha"] or 0,
                    "last_attendance_date": (
                        str(stats["last_attendance_date"])
                        if stats["last_attendance_date"]
                        else None
                    ),
                },
                "attended_today": today_attendance is not None,
                "recent_attendance": formatted_recent,  # <-- PERBAIKAN: gunakan formatted_recent, bukan recent
            }
        )

    except Exception as e:
        logger.error(f"Get student detail error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# ADD NEW STUDENT
# ===========================================
@students_bp.route("/add", methods=["POST"])
@token_required
def add_student():
    """Add new student"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["nis", "nisn", "nama", "kelas_id", "gender"]
        for field in required_fields:
            if field not in data or not data[field]:
                return (
                    jsonify({"success": False, "message": f"{field} harus diisi"}),
                    400,
                )

        nis = data["nis"].strip()
        nisn = data["nisn"].strip()
        nama = data["nama"].strip()
        kelas_id = data["kelas_id"]
        gender = data["gender"].strip().upper()

        # Validate gender
        if gender not in ["L", "P"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Gender harus L (Laki-laki) atau P (Perempuan)",
                    }
                ),
                400,
            )

        # Validate NISN format
        if not (nisn.isdigit() and len(nisn) == 10):
            return (
                jsonify({"success": False, "message": "NISN harus 10 digit angka"}),
                400,
            )

        # Check if NIS already exists
        existing = fetch_one("SELECT id FROM siswa WHERE nis = %s", (nis,))
        if existing:
            return (
                jsonify({"success": False, "message": f"NIS {nis} sudah terdaftar"}),
                409,
            )

        # Check if kelas exists
        kelas = fetch_one("SELECT id FROM kelas WHERE id = %s", (kelas_id,))
        if not kelas:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Kelas dengan ID {kelas_id} tidak ditemukan",
                    }
                ),
                404,
            )

        # Insert new student
        result = execute(
            "INSERT INTO siswa (nis, nisn, nama, kelas_id, gender) VALUES (%s, %s, %s, %s, %s)",
            (nis, nisn, nama, kelas_id, gender),
            commit=True,
        )

        if not result["success"]:
            return (
                jsonify({"success": False, "message": "Gagal menambahkan siswa"}),
                500,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Siswa berhasil ditambahkan",
                    "student": {
                        "id": result.get("last_id"),
                        "nis": nis,
                        "nisn": nisn,
                        "nama": nama,
                        "kelas_id": kelas_id,
                        "gender": gender,
                        "gender_label": "Laki-laki" if gender == "L" else "Perempuan",
                    },
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Add student error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# UPDATE STUDENT
# ===========================================
@students_bp.route("/<nis>", methods=["PUT"])
@token_required
def update_student(nis):
    """Update student data"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "Data tidak ditemukan"}), 400

        # Check if student exists
        existing = fetch_one("SELECT id FROM siswa WHERE nis = %s", (nis,))
        if not existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Siswa dengan NIS {nis} tidak ditemukan",
                    }
                ),
                404,
            )

        # Build update query dynamically
        update_fields = []
        params = []

        if "nama" in data and data["nama"]:
            update_fields.append("nama = %s")
            params.append(data["nama"].strip())

        if "kelas_id" in data and data["kelas_id"]:
            # Validate kelas exists
            kelas = fetch_one("SELECT id FROM kelas WHERE id = %s", (data["kelas_id"],))
            if not kelas:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Kelas dengan ID {data['kelas_id']} tidak ditemukan",
                        }
                    ),
                    404,
                )
            update_fields.append("kelas_id = %s")
            params.append(data["kelas_id"])

        if "gender" in data and data["gender"]:
            gender = data["gender"].strip().upper()
            if gender not in ["L", "P"]:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Gender harus L (Laki-laki) atau P (Perempuan)",
                        }
                    ),
                    400,
                )
            update_fields.append("gender = %s")
            params.append(gender)

        if "nisn" in data and data["nisn"]:
            nisn = data["nisn"].strip()
            if not (nisn.isdigit() and len(nisn) == 10):
                return (
                    jsonify({"success": False, "message": "NISN harus 10 digit angka"}),
                    400,
                )
            update_fields.append("nisn = %s")
            params.append(nisn)

        if not update_fields:
            return (
                jsonify({"success": False, "message": "Tidak ada data yang diupdate"}),
                400,
            )

        # Execute update
        params.append(nis)
        query = f"UPDATE siswa SET {', '.join(update_fields)} WHERE nis = %s"
        result = execute(query, tuple(params), commit=True)

        if not result["success"]:
            return jsonify({"success": False, "message": "Gagal mengupdate data"}), 500

        # Get updated data
        updated = fetch_one(
            """
            SELECT nis, nisn, nama, kelas_id, gender 
            FROM siswa WHERE nis = %s
        """,
            (nis,),
        )

        return jsonify(
            {
                "success": True,
                "message": "Data siswa berhasil diperbarui",
                "student": {
                    "nis": updated["nis"],
                    "nisn": updated["nisn"],
                    "nama": updated["nama"],
                    "kelas_id": updated["kelas_id"],
                    "gender": updated["gender"],
                    "gender_label": (
                        "Laki-laki" if updated["gender"] == "L" else "Perempuan"
                    ),
                },
            }
        )

    except Exception as e:
        logger.error(f"Update student error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# DELETE STUDENT
# ===========================================
@students_bp.route("/<nis>", methods=["DELETE"])
@token_required
def delete_student(nis):
    """Delete student"""
    try:
        # Check if student exists
        student = fetch_one("SELECT id, nama FROM siswa WHERE nis = %s", (nis,))
        if not student:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Siswa dengan NIS {nis} tidak ditemukan",
                    }
                ),
                404,
            )

        # Check if student has attendance records
        attendance = fetch_one(
            "SELECT id FROM absensi WHERE siswa_id = %s LIMIT 1", (student["id"],)
        )

        if attendance:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Siswa tidak dapat dihapus karena memiliki riwayat absensi",
                    }
                ),
                409,
            )

        # Delete student
        result = execute("DELETE FROM siswa WHERE nis = %s", (nis,), commit=True)

        if not result["success"] or result.get("rowcount", 0) == 0:
            return jsonify({"success": False, "message": "Gagal menghapus siswa"}), 500

        return jsonify(
            {"success": True, "message": f"Siswa {student['nama']} berhasil dihapus"}
        )

    except Exception as e:
        logger.error(f"Delete student error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET STUDENTS BY KELAS
# ===========================================
@students_bp.route("/by-kelas/<int:kelas_id>", methods=["GET"])
@token_required
def get_students_by_kelas(kelas_id):
    """Get all students in a specific class"""
    try:
        # Get class info
        kelas = fetch_one(
            """
            SELECT 
                k.id, k.nama_kelas, k.tingkat,
                j.nama as jurusan,
                g.nama as wali_kelas
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            WHERE k.id = %s
        """,
            (kelas_id,),
        )

        if not kelas:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Kelas dengan ID {kelas_id} tidak ditemukan",
                    }
                ),
                404,
            )

        # Get students
        students = fetch_all(
            """
            SELECT 
                id, nis, nisn, nama, gender, card_version
            FROM siswa 
            WHERE kelas_id = %s
            ORDER BY nama
        """,
            (kelas_id,),
        )

        # Add gender labels
        for student in students:
            student["gender_label"] = (
                "Laki-laki"
                if student["gender"] == "L"
                else "Perempuan" if student["gender"] == "P" else "-"
            )

        return jsonify(
            {
                "success": True,
                "kelas": kelas,
                "total_siswa": len(students),
                "students": students,
            }
        )

    except Exception as e:
        logger.error(f"Get students by kelas error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# CHECK NISN VALIDITY
# ===========================================
@students_bp.route("/check-nisn", methods=["GET"])
@token_required
def check_nisn_validity():
    """Check if students have valid NISN (10 digits)"""
    try:
        students = fetch_all(
            """
            SELECT
                nis,
                nisn,
                nama,
                kelas_id,
                k.nama_kelas as kelas,
                CASE
                    WHEN nisn IS NULL OR nisn = '' THEN 'TIDAK ADA'
                    WHEN LENGTH(TRIM(nisn)) != 10 THEN 'TIDAK VALID'
                    WHEN TRIM(nisn) NOT REGEXP '^[0-9]{10}$' THEN 'TIDAK VALID'
                    ELSE 'VALID'
                END as status_nisn,
                LENGTH(TRIM(nisn)) as panjang_nisn
            FROM siswa s
            LEFT JOIN kelas k ON s.kelas_id = k.id
            ORDER BY k.nama_kelas, s.nama
        """
        )

        # Calculate statistics
        valid = sum(1 for s in students if s["status_nisn"] == "VALID")
        invalid = sum(1 for s in students if s["status_nisn"] == "TIDAK VALID")
        missing = sum(1 for s in students if s["status_nisn"] == "TIDAK ADA")

        return jsonify(
            {
                "success": True,
                "total": len(students),
                "valid_nisn": valid,
                "invalid_nisn": invalid,
                "missing_nisn": missing,
                "students": students,
            }
        )

    except Exception as e:
        logger.error(f"Check NISN error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET STUDENT STATISTICS BY KELAS
# ===========================================
@students_bp.route("/statistics/by-kelas", methods=["GET"])
@token_required
def get_statistics_by_kelas():
    """Get student statistics grouped by class"""
    try:
        statistics = fetch_all(
            """
            SELECT 
                k.id as kelas_id,
                k.nama_kelas,
                k.tingkat,
                j.nama as jurusan,
                COUNT(s.id) as total_siswa,
                SUM(CASE WHEN s.gender = 'L' THEN 1 ELSE 0 END) as laki_laki,
                SUM(CASE WHEN s.gender = 'P' THEN 1 ELSE 0 END) as perempuan
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN siswa s ON k.id = s.kelas_id
            GROUP BY k.id, k.nama_kelas, k.tingkat, j.nama
            ORDER BY k.tingkat, j.nama, k.nama_kelas
        """
        )

        # Calculate totals
        total_siswa = sum(s["total_siswa"] or 0 for s in statistics)
        total_laki = sum(s["laki_laki"] or 0 for s in statistics)
        total_perempuan = sum(s["perempuan"] or 0 for s in statistics)

        return jsonify(
            {
                "success": True,
                "total_kelas": len(statistics),
                "total_siswa": total_siswa,
                "total_laki_laki": total_laki,
                "total_perempuan": total_perempuan,
                "statistics": statistics,
            }
        )

    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
