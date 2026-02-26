# blueprints/teachers.py
from flask import Blueprint, request, jsonify
from utils.database import fetch_one, fetch_all, execute
from utils.auth import token_required
import logging

teachers_bp = Blueprint('teachers', __name__, url_prefix='/api/guru')
logger = logging.getLogger(__name__)


# ===========================================
# GET ALL TEACHERS
# ===========================================
@teachers_bp.route('', methods=['GET'])
@token_required
def get_all_teachers():
    """Get all teachers"""
    try:
        teachers = fetch_all("""
            SELECT id, nip, nama, telp, email 
            FROM guru 
            ORDER BY nama
        """)

        return jsonify({
            "success": True,
            "data": teachers,
            "total": len(teachers)
        })

    except Exception as e:
        logger.error(f"Get all teachers error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET TEACHER BY ID
# ===========================================
@teachers_bp.route('/<int:id>', methods=['GET'])
@token_required
def get_teacher_by_id(id):
    """Get teacher by ID"""
    try:
        teacher = fetch_one("""
            SELECT id, nip, nama, telp, email 
            FROM guru 
            WHERE id = %s
        """, (id,))

        if not teacher:
            return jsonify({
                "success": False,
                "message": f"Guru dengan ID {id} tidak ditemukan"
            }), 404

        return jsonify({
            "success": True,
            "data": teacher
        })

    except Exception as e:
        logger.error(f"Get teacher by ID error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET TEACHER BY NIP
# ===========================================
@teachers_bp.route('/nip/<nip>', methods=['GET'])
@token_required
def get_teacher_by_nip(nip):
    """Get teacher by NIP"""
    try:
        teacher = fetch_one("""
            SELECT id, nip, nama, telp, email 
            FROM guru 
            WHERE nip = %s
        """, (nip,))

        if not teacher:
            return jsonify({
                "success": False,
                "message": f"Guru dengan NIP {nip} tidak ditemukan"
            }), 404

        return jsonify({
            "success": True,
            "data": teacher
        })

    except Exception as e:
        logger.error(f"Get teacher by NIP error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# ADD NEW TEACHER
# ===========================================
@teachers_bp.route('', methods=['POST'])
@token_required
def add_teacher():
    """Add new teacher"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'nama' not in data or not data['nama']:
            return jsonify({
                "success": False,
                "message": "Nama guru harus diisi"
            }), 400

        nama = data['nama'].strip()
        nip = data.get('nip', '').strip() or None
        telp = data.get('telp', '').strip() or None
        email = data.get('email', '').strip() or None

        # Validate email format if provided
        if email and '@' not in email:
            return jsonify({
                "success": False,
                "message": "Format email tidak valid"
            }), 400

        # Check if NIP already exists (if provided)
        if nip:
            existing = fetch_one("SELECT id FROM guru WHERE nip = %s", (nip,))
            if existing:
                return jsonify({
                    "success": False,
                    "message": f"NIP {nip} sudah terdaftar"
                }), 409

        # Insert new teacher
        result = execute("""
            INSERT INTO guru (nip, nama, telp, email) 
            VALUES (%s, %s, %s, %s)
        """, (nip, nama, telp, email), commit=True)

        if not result['success']:
            return jsonify({
                "success": False,
                "message": "Gagal menambahkan guru"
            }), 500

        return jsonify({
            "success": True,
            "message": "Guru berhasil ditambahkan",
            "data": {
                "id": result.get('last_id'),
                "nip": nip,
                "nama": nama,
                "telp": telp,
                "email": email
            }
        }), 201

    except Exception as e:
        logger.error(f"Add teacher error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# UPDATE TEACHER
# ===========================================
@teachers_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_teacher(id):
    """Update teacher data"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "Data tidak ditemukan"}), 400

        # Check if teacher exists
        existing = fetch_one("SELECT id FROM guru WHERE id = %s", (id,))
        if not existing:
            return jsonify({
                "success": False,
                "message": f"Guru dengan ID {id} tidak ditemukan"
            }), 404

        # Build update query
        update_fields = []
        params = []

        if 'nama' in data and data['nama']:
            update_fields.append("nama = %s")
            params.append(data['nama'].strip())

        if 'nip' in data:
            if data['nip']:
                # Check if NIP already used by another teacher
                duplicate = fetch_one("""
                    SELECT id FROM guru 
                    WHERE nip = %s AND id != %s
                """, (data['nip'].strip(), id))
                if duplicate:
                    return jsonify({
                        "success": False,
                        "message": f"NIP {data['nip']} sudah digunakan"
                    }), 409
                update_fields.append("nip = %s")
                params.append(data['nip'].strip())
            else:
                update_fields.append("nip = NULL")
                # No param needed for NULL

        if 'telp' in data:
            if data['telp']:
                update_fields.append("telp = %s")
                params.append(data['telp'].strip())
            else:
                update_fields.append("telp = NULL")

        if 'email' in data:
            if data['email']:
                # Validate email format
                if '@' not in data['email']:
                    return jsonify({
                        "success": False,
                        "message": "Format email tidak valid"
                    }), 400
                update_fields.append("email = %s")
                params.append(data['email'].strip())
            else:
                update_fields.append("email = NULL")

        if not update_fields:
            return jsonify({
                "success": False,
                "message": "Tidak ada data yang diupdate"
            }), 400

        # Execute update
        params.append(id)
        query = f"UPDATE guru SET {', '.join(update_fields)} WHERE id = %s"
        result = execute(query, tuple(params), commit=True)

        if not result['success']:
            return jsonify({"success": False, "message": "Gagal mengupdate guru"}), 500

        # Get updated data
        updated = fetch_one("""
            SELECT id, nip, nama, telp, email 
            FROM guru WHERE id = %s
        """, (id,))

        return jsonify({
            "success": True,
            "message": "Data guru berhasil diperbarui",
            "data": updated
        })

    except Exception as e:
        logger.error(f"Update teacher error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# DELETE TEACHER
# ===========================================
@teachers_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_teacher(id):
    """Delete teacher"""
    try:
        # Check if teacher exists
        teacher = fetch_one("SELECT id, nama FROM guru WHERE id = %s", (id,))
        if not teacher:
            return jsonify({
                "success": False,
                "message": f"Guru dengan ID {id} tidak ditemukan"
            }), 404

        # Check if teacher is homeroom teacher for any class
        wali_kelas = fetch_all("""
            SELECT id, nama_kelas FROM kelas 
            WHERE wali_kelas_id = %s
        """, (id,))

        if wali_kelas:
            kelas_list = [f"{k['nama_kelas']}" for k in wali_kelas]
            return jsonify({
                "success": False,
                "message": f"Guru tidak dapat dihapus karena menjadi wali kelas: {', '.join(kelas_list)}",
                "wali_kelas": wali_kelas
            }), 409

        # Delete teacher
        result = execute("DELETE FROM guru WHERE id = %s", (id,), commit=True)

        if not result['success'] or result.get('rowcount', 0) == 0:
            return jsonify({
                "success": False,
                "message": "Gagal menghapus guru"
            }), 500

        return jsonify({
            "success": True,
            "message": f"Guru {teacher['nama']} berhasil dihapus"
        })

    except Exception as e:
        logger.error(f"Delete teacher error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# SEARCH TEACHERS
# ===========================================
@teachers_bp.route('/search', methods=['GET'])
@token_required
def search_teachers():
    """Search teachers by name or NIP"""
    try:
        keyword = request.args.get('q', '')

        if not keyword or len(keyword) < 2:
            return jsonify({
                "success": False,
                "message": "Kata kunci minimal 2 karakter"
            }), 400

        search_term = f"%{keyword}%"
        teachers = fetch_all("""
            SELECT id, nip, nama, telp, email 
            FROM guru 
            WHERE nama LIKE %s OR nip LIKE %s
            ORDER BY nama
            LIMIT 50
        """, (search_term, search_term))

        return jsonify({
            "success": True,
            "keyword": keyword,
            "total": len(teachers),
            "data": teachers
        })

    except Exception as e:
        logger.error(f"Search teachers error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET TEACHERS WITH CLASSES (Wali Kelas)
# ===========================================
@teachers_bp.route('/with-kelas', methods=['GET'])
@token_required
def get_teachers_with_classes():
    """Get all teachers with their homeroom classes"""
    try:
        # Get all teachers
        teachers = fetch_all("""
            SELECT id, nip, nama, telp, email 
            FROM guru 
            ORDER BY nama
        """)

        # For each teacher, get their homeroom classes
        result = []
        for teacher in teachers:
            classes = fetch_all("""
                SELECT 
                    k.id as kelas_id,
                    k.nama_kelas,
                    k.tingkat,
                    k.tahun_ajaran,
                    j.id as jurusan_id,
                    j.nama as jurusan_nama,
                    j.kode as jurusan_kode,
                    (SELECT COUNT(*) FROM siswa WHERE kelas_id = k.id) as jumlah_siswa
                FROM kelas k
                LEFT JOIN jurusan j ON k.jurusan_id = j.id
                WHERE k.wali_kelas_id = %s
                ORDER BY k.tingkat, j.kode, k.nama_kelas
            """, (teacher['id'],))

            # Add tingkat label
            for kelas in classes:
                kelas['tingkat_label'] = get_tingkat_label(kelas['tingkat'])

            teacher['wali_kelas'] = classes
            result.append(teacher)

        return jsonify({
            "success": True,
            "total": len(result),
            "data": result
        })

    except Exception as e:
        logger.error(f"Get teachers with classes error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET TEACHER STATISTICS
# ===========================================
@teachers_bp.route('/statistics', methods=['GET'])
@token_required
def get_teacher_statistics():
    """Get teacher statistics"""
    try:
        # Total teachers
        total = fetch_one("SELECT COUNT(*) as total FROM guru")

        # Teachers with homeroom classes
        with_homeroom = fetch_one("""
            SELECT COUNT(DISTINCT wali_kelas_id) as total 
            FROM kelas 
            WHERE wali_kelas_id IS NOT NULL
        """)

        # Teachers with contact info
        with_contact = fetch_one("""
            SELECT COUNT(*) as total 
            FROM guru 
            WHERE telp IS NOT NULL OR email IS NOT NULL
        """)

        # Distribution by homeroom
        homeroom_distribution = fetch_all("""
            SELECT 
                g.id,
                g.nama,
                COUNT(k.id) as jumlah_kelas
            FROM guru g
            LEFT JOIN kelas k ON g.id = k.wali_kelas_id
            GROUP BY g.id, g.nama
            ORDER BY jumlah_kelas DESC
            LIMIT 10
        """)

        return jsonify({
            "success": True,
            "statistics": {
                "total_guru": total['total'] if total else 0,
                "guru_wali_kelas": with_homeroom['total'] if with_homeroom else 0,
                "guru_dengan_kontak": with_contact['total'] if with_contact else 0,
                "guru_tanpa_kontak": (total['total'] if total else 0) - (with_contact['total'] if with_contact else 0),
                "total_kelas_diampu": sum(h['jumlah_kelas'] for h in homeroom_distribution)
            },
            "homeroom_distribution": homeroom_distribution
        })

    except Exception as e:
        logger.error(f"Get teacher statistics error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# BULK IMPORT TEACHERS
# ===========================================
@teachers_bp.route('/bulk-import', methods=['POST'])
@token_required
def bulk_import_teachers():
    """Bulk import teachers from array"""
    try:
        data = request.get_json()

        if not data or 'teachers' not in data:
            return jsonify({
                "success": False,
                "message": "Data teachers diperlukan"
            }), 400

        teachers_list = data['teachers']
        if not isinstance(teachers_list, list):
            return jsonify({
                "success": False,
                "message": "teachers harus berupa array"
            }), 400

        if len(teachers_list) > 100:
            return jsonify({
                "success": False,
                "message": "Maksimal 100 guru per batch"
            }), 400

        results = []
        success_count = 0
        error_count = 0

        for teacher_data in teachers_list:
            # Validate required fields
            if 'nama' not in teacher_data or not teacher_data['nama']:
                results.append({
                    "data": teacher_data,
                    "success": False,
                    "error": "Nama guru harus diisi"
                })
                error_count += 1
                continue

            nama = teacher_data['nama'].strip()
            nip = teacher_data.get('nip', '').strip() or None
            telp = teacher_data.get('telp', '').strip() or None
            email = teacher_data.get('email', '').strip() or None

            # Validate email format if provided
            if email and '@' not in email:
                results.append({
                    "data": teacher_data,
                    "success": False,
                    "error": f"Format email tidak valid: {email}"
                })
                error_count += 1
                continue

            # Check duplicate NIP if provided
            if nip:
                existing = fetch_one("SELECT id FROM guru WHERE nip = %s", (nip,))
                if existing:
                    results.append({
                        "data": teacher_data,
                        "success": False,
                        "error": f"NIP {nip} sudah terdaftar"
                    })
                    error_count += 1
                    continue

            # Insert teacher
            result = execute("""
                INSERT INTO guru (nip, nama, telp, email) 
                VALUES (%s, %s, %s, %s)
            """, (nip, nama, telp, email), commit=True)

            if result['success']:
                results.append({
                    "data": {
                        "id": result.get('last_id'),
                        "nip": nip,
                        "nama": nama,
                        "telp": telp,
                        "email": email
                    },
                    "success": True
                })
                success_count += 1
            else:
                results.append({
                    "data": teacher_data,
                    "success": False,
                    "error": "Gagal menyimpan ke database"
                })
                error_count += 1

        return jsonify({
            "success": True,
            "total": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        })

    except Exception as e:
        logger.error(f"Bulk import teachers error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# EXPORT TEACHERS (CSV format)
# ===========================================
@teachers_bp.route('/export', methods=['GET'])
@token_required
def export_teachers():
    """Export teachers data (returns JSON for now, can be modified for CSV)"""
    try:
        format_type = request.args.get('format', 'json')

        teachers = fetch_all("""
            SELECT 
                g.id,
                g.nip,
                g.nama,
                g.telp,
                g.email,
                GROUP_CONCAT(k.nama_kelas SEPARATOR ', ') as wali_kelas
            FROM guru g
            LEFT JOIN kelas k ON g.id = k.wali_kelas_id
            GROUP BY g.id, g.nip, g.nama, g.telp, g.email
            ORDER BY g.nama
        """)

        if format_type == 'csv':
            # Convert to CSV format
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(['ID', 'NIP', 'Nama', 'Telepon', 'Email', 'Wali Kelas'])

            # Write data
            for teacher in teachers:
                writer.writerow([
                    teacher['id'],
                    teacher['nip'] or '',
                    teacher['nama'],
                    teacher['telp'] or '',
                    teacher['email'] or '',
                    teacher['wali_kelas'] or ''
                ])

            csv_data = output.getvalue()
            output.close()

            return jsonify({
                "success": True,
                "format": "csv",
                "data": csv_data,
                "filename": f"guru_{datetime.now().strftime('%Y%m%d')}.csv"
            })

        # Default JSON format
        return jsonify({
            "success": True,
            "total": len(teachers),
            "data": teachers
        })

    except Exception as e:
        logger.error(f"Export teachers error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# HELPER FUNCTIONS
# ===========================================
def get_tingkat_label(tingkat):
    """Convert tingkat number to readable label"""
    map_label = {
        '1': 'X (10)',
        '2': 'XI (11)',
        '3': 'XII (12)'
    }
    return map_label.get(str(tingkat), str(tingkat))
