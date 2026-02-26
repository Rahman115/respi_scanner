# blueprints/classes.py
from flask import Blueprint, request, jsonify
from utils.database import fetch_one, fetch_all, execute
from utils.auth import token_required
import logging

classes_bp = Blueprint('classes', __name__, url_prefix='/api/kelas')
logger = logging.getLogger(__name__)


# ===========================================
# GET ALL CLASSES
# ===========================================
@classes_bp.route('', methods=['GET'])
@token_required
def get_all_classes():
    """Get all classes with jurusan and wali kelas info"""
    try:
        classes = fetch_all("""
            SELECT 
                k.id,
                k.jurusan_id,
                j.kode as jurusan_kode,
                j.nama as jurusan_nama,
                k.tingkat,
                k.nama_kelas,
                k.wali_kelas_id,
                g.nama as wali_kelas_nama,
                g.nip as wali_kelas_nip,
                k.tahun_ajaran,
                (SELECT COUNT(*) FROM siswa WHERE kelas_id = k.id) as jumlah_siswa
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            ORDER BY k.tingkat, j.kode, k.nama_kelas
        """)

        # Add tingkat label
        for kelas in classes:
            kelas['tingkat_label'] = get_tingkat_label(kelas['tingkat'])

        return jsonify({
            "success": True,
            "data": classes,
            "total": len(classes)
        })

    except Exception as e:
        logger.error(f"Get all classes error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET CLASS BY ID
# ===========================================
@classes_bp.route('/<int:id>', methods=['GET'])
@token_required
def get_class_by_id(id):
    """Get class details by ID"""
    try:
        kelas = fetch_one("""
            SELECT 
                k.id,
                k.jurusan_id,
                j.kode as jurusan_kode,
                j.nama as jurusan_nama,
                k.tingkat,
                k.nama_kelas,
                k.wali_kelas_id,
                g.nama as wali_kelas_nama,
                g.nip as wali_kelas_nip,
                g.telp as wali_kelas_telp,
                g.email as wali_kelas_email,
                k.tahun_ajaran,
                (SELECT COUNT(*) FROM siswa WHERE kelas_id = k.id) as jumlah_siswa
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            WHERE k.id = %s
        """, (id,))

        if not kelas:
            return jsonify({
                "success": False,
                "message": f"Kelas dengan ID {id} tidak ditemukan"
            }), 404

        kelas['tingkat_label'] = get_tingkat_label(kelas['tingkat'])

        return jsonify({
            "success": True,
            "data": kelas
        })

    except Exception as e:
        logger.error(f"Get class by ID error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET CLASSES BY JURUSAN
# ===========================================
@classes_bp.route('/by-jurusan/<int:jurusan_id>', methods=['GET'])
@token_required
def get_classes_by_jurusan(jurusan_id):
    """Get classes by jurusan ID"""
    try:
        tingkat = request.args.get('tingkat')

        query = """
            SELECT 
                k.id,
                k.jurusan_id,
                j.kode as jurusan_kode,
                j.nama as jurusan_nama,
                k.tingkat,
                k.nama_kelas,
                k.wali_kelas_id,
                g.nama as wali_kelas_nama,
                k.tahun_ajaran,
                (SELECT COUNT(*) FROM siswa WHERE kelas_id = k.id) as jumlah_siswa
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            WHERE k.jurusan_id = %s
        """
        params = [jurusan_id]

        if tingkat:
            query += " AND k.tingkat = %s"
            params.append(tingkat)

        query += " ORDER BY k.tingkat, k.nama_kelas"

        classes = fetch_all(query, tuple(params))

        for kelas in classes:
            kelas['tingkat_label'] = get_tingkat_label(kelas['tingkat'])

        return jsonify({
            "success": True,
            "data": classes,
            "total": len(classes)
        })

    except Exception as e:
        logger.error(f"Get classes by jurusan error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET CLASSES BY TINGKAT
# ===========================================
@classes_bp.route('/by-tingkat/<tingkat>', methods=['GET'])
@token_required
def get_classes_by_tingkat(tingkat):
    """Get classes by tingkat (1/2/3 or X/XI/XII)"""
    try:
        # Convert if using X/XI/XII format
        tingkat_map = {'X': '1', 'XI': '2', 'XII': '3'}
        db_tingkat = tingkat_map.get(tingkat, tingkat)

        if db_tingkat not in ['1', '2', '3']:
            return jsonify({
                "success": False,
                "message": "Tingkat harus 1/2/3 atau X/XI/XII"
            }), 400

        classes = fetch_all("""
            SELECT 
                k.id,
                k.jurusan_id,
                j.kode as jurusan_kode,
                j.nama as jurusan_nama,
                k.tingkat,
                k.nama_kelas,
                k.wali_kelas_id,
                g.nama as wali_kelas_nama,
                k.tahun_ajaran,
                (SELECT COUNT(*) FROM siswa WHERE kelas_id = k.id) as jumlah_siswa
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            WHERE k.tingkat = %s
            ORDER BY j.kode, k.nama_kelas
        """, (db_tingkat,))

        for kelas in classes:
            kelas['tingkat_label'] = get_tingkat_label(kelas['tingkat'])

        return jsonify({
            "success": True,
            "data": classes,
            "total": len(classes)
        })

    except Exception as e:
        logger.error(f"Get classes by tingkat error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET CLASSES BY WALI KELAS
# ===========================================
@classes_bp.route('/wali-kelas/<int:guru_id>', methods=['GET'])
@token_required
def get_classes_by_wali_kelas(guru_id):
    """Get classes taught by a specific homeroom teacher"""
    try:
        classes = fetch_all("""
            SELECT 
                k.id,
                k.jurusan_id,
                j.kode as jurusan_kode,
                j.nama as jurusan_nama,
                k.tingkat,
                k.nama_kelas,
                k.wali_kelas_id,
                g.nama as wali_kelas_nama,
                k.tahun_ajaran,
                (SELECT COUNT(*) FROM siswa WHERE kelas_id = k.id) as jumlah_siswa
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            WHERE k.wali_kelas_id = %s
            ORDER BY k.tingkat, j.kode, k.nama_kelas
        """, (guru_id,))

        for kelas in classes:
            kelas['tingkat_label'] = get_tingkat_label(kelas['tingkat'])

        return jsonify({
            "success": True,
            "data": classes,
            "total": len(classes)
        })

    except Exception as e:
        logger.error(f"Get classes by wali kelas error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# ADD NEW CLASS
# ===========================================
@classes_bp.route('', methods=['POST'])
@token_required
def add_class():
    """Add new class"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["jurusan_id", "tingkat", "nama_kelas", "tahun_ajaran"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "message": f"Field {field} harus diisi"
                }), 400

        jurusan_id = data["jurusan_id"]
        tingkat = data["tingkat"]
        nama_kelas = data["nama_kelas"].strip()
        tahun_ajaran = data["tahun_ajaran"].strip()
        wali_kelas_id = data.get("wali_kelas_id")

        # Validate tingkat
        if tingkat not in ['1', '2', '3']:
            return jsonify({
                "success": False,
                "message": "Tingkat harus 1, 2, atau 3"
            }), 400

        # Check if jurusan exists
        jurusan = fetch_one("SELECT id FROM jurusan WHERE id = %s", (jurusan_id,))
        if not jurusan:
            return jsonify({
                "success": False,
                "message": f"Jurusan dengan ID {jurusan_id} tidak ditemukan"
            }), 404

        # Check if wali kelas exists (if provided)
        if wali_kelas_id:
            wali_kelas = fetch_one("SELECT id FROM guru WHERE id = %s", (wali_kelas_id,))
            if not wali_kelas:
                return jsonify({
                    "success": False,
                    "message": f"Guru dengan ID {wali_kelas_id} tidak ditemukan"
                }), 404

        # Check for duplicate class
        existing = fetch_one("""
            SELECT id FROM kelas 
            WHERE jurusan_id = %s AND tingkat = %s AND nama_kelas = %s
        """, (jurusan_id, tingkat, nama_kelas))

        if existing:
            return jsonify({
                "success": False,
                "message": f"Kelas {nama_kelas} sudah terdaftar untuk jurusan ini"
            }), 409

        # Insert new class
        result = execute("""
            INSERT INTO kelas (jurusan_id, tingkat, nama_kelas, wali_kelas_id, tahun_ajaran)
            VALUES (%s, %s, %s, %s, %s)
        """, (jurusan_id, tingkat, nama_kelas, wali_kelas_id, tahun_ajaran), commit=True)

        if not result['success']:
            return jsonify({
                "success": False,
                "message": "Gagal menambahkan kelas"
            }), 500

        return jsonify({
            "success": True,
            "message": "Kelas berhasil ditambahkan",
            "data": {
                "id": result.get('last_id'),
                "jurusan_id": jurusan_id,
                "tingkat": tingkat,
                "tingkat_label": get_tingkat_label(tingkat),
                "nama_kelas": nama_kelas,
                "wali_kelas_id": wali_kelas_id,
                "tahun_ajaran": tahun_ajaran
            }
        }), 201

    except Exception as e:
        logger.error(f"Add class error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# UPDATE CLASS
# ===========================================
@classes_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_class(id):
    """Update class data"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "Data tidak ditemukan"}), 400

        # Check if class exists
        existing = fetch_one("SELECT * FROM kelas WHERE id = %s", (id,))
        if not existing:
            return jsonify({
                "success": False,
                "message": f"Kelas dengan ID {id} tidak ditemukan"
            }), 404

        # Build update query
        update_fields = []
        params = []

        if 'jurusan_id' in data and data['jurusan_id']:
            # Check if jurusan exists
            jurusan = fetch_one("SELECT id FROM jurusan WHERE id = %s", (data['jurusan_id'],))
            if not jurusan:
                return jsonify({
                    "success": False,
                    "message": f"Jurusan dengan ID {data['jurusan_id']} tidak ditemukan"
                }), 404
            update_fields.append("jurusan_id = %s")
            params.append(data['jurusan_id'])

        if 'tingkat' in data and data['tingkat']:
            if data['tingkat'] not in ['1', '2', '3']:
                return jsonify({
                    "success": False,
                    "message": "Tingkat harus 1, 2, atau 3"
                }), 400
            update_fields.append("tingkat = %s")
            params.append(data['tingkat'])

        if 'nama_kelas' in data and data['nama_kelas']:
            update_fields.append("nama_kelas = %s")
            params.append(data['nama_kelas'].strip())

        if 'tahun_ajaran' in data and data['tahun_ajaran']:
            update_fields.append("tahun_ajaran = %s")
            params.append(data['tahun_ajaran'].strip())

        if 'wali_kelas_id' in data:
            if data['wali_kelas_id']:
                # Check if guru exists
                guru = fetch_one("SELECT id FROM guru WHERE id = %s", (data['wali_kelas_id'],))
                if not guru:
                    return jsonify({
                        "success": False,
                        "message": f"Guru dengan ID {data['wali_kelas_id']} tidak ditemukan"
                    }), 404
                update_fields.append("wali_kelas_id = %s")
                params.append(data['wali_kelas_id'])
            else:
                update_fields.append("wali_kelas_id = NULL")
                # No param needed for NULL

        if not update_fields:
            return jsonify({
                "success": False,
                "message": "Tidak ada data yang diupdate"
            }), 400

        # Check for duplicate if changing unique fields
        if any(f.startswith('jurusan_id') or f.startswith('tingkat') or f.startswith('nama_kelas') for f in update_fields):
            new_jurusan_id = None
            new_tingkat = None
            new_nama_kelas = None

            # Get new values from update fields
            for i, field in enumerate(update_fields):
                if field.startswith('jurusan_id'):
                    new_jurusan_id = params[i]
                elif field.startswith('tingkat'):
                    new_tingkat = params[i]
                elif field.startswith('nama_kelas'):
                    new_nama_kelas = params[i]

            # Use existing values if not updated
            if new_jurusan_id is None:
                new_jurusan_id = existing['jurusan_id']
            if new_tingkat is None:
                new_tingkat = existing['tingkat']
            if new_nama_kelas is None:
                new_nama_kelas = existing['nama_kelas']

            # Check duplicate
            duplicate = fetch_one("""
                SELECT id FROM kelas 
                WHERE jurusan_id = %s AND tingkat = %s AND nama_kelas = %s AND id != %s
            """, (new_jurusan_id, new_tingkat, new_nama_kelas, id))

            if duplicate:
                return jsonify({
                    "success": False,
                    "message": f"Kelas {new_nama_kelas} sudah terdaftar untuk jurusan ini"
                }), 409

        # Execute update
        params.append(id)
        query = f"UPDATE kelas SET {', '.join(update_fields)} WHERE id = %s"
        result = execute(query, tuple(params), commit=True)

        if not result['success']:
            return jsonify({"success": False, "message": "Gagal mengupdate kelas"}), 500

        # Get updated data
        updated = fetch_one("""
            SELECT 
                k.id, k.jurusan_id, j.nama as jurusan_nama, j.kode as jurusan_kode,
                k.tingkat, k.nama_kelas, k.wali_kelas_id, g.nama as wali_kelas_nama,
                k.tahun_ajaran
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            WHERE k.id = %s
        """, (id,))

        updated['tingkat_label'] = get_tingkat_label(updated['tingkat'])

        return jsonify({
            "success": True,
            "message": "Kelas berhasil diupdate",
            "data": updated
        })

    except Exception as e:
        logger.error(f"Update class error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# DELETE CLASS
# ===========================================
@classes_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_class(id):
    """Delete class"""
    try:
        # Check if class exists
        kelas = fetch_one("SELECT id, nama_kelas FROM kelas WHERE id = %s", (id,))
        if not kelas:
            return jsonify({
                "success": False,
                "message": f"Kelas dengan ID {id} tidak ditemukan"
            }), 404

        # Check if class has students
        students = fetch_one(
            "SELECT COUNT(*) as total FROM siswa WHERE kelas_id = %s",
            (id,)
        )

        if students and students['total'] > 0:
            return jsonify({
                "success": False,
                "message": f"Kelas tidak dapat dihapus karena masih memiliki {students['total']} siswa",
                "siswa_count": students['total']
            }), 409

        # Delete class
        result = execute("DELETE FROM kelas WHERE id = %s", (id,), commit=True)

        if not result['success'] or result.get('rowcount', 0) == 0:
            return jsonify({
                "success": False,
                "message": "Gagal menghapus kelas"
            }), 500

        return jsonify({
            "success": True,
            "message": f"Kelas {kelas['nama_kelas']} berhasil dihapus"
        })

    except Exception as e:
        logger.error(f"Delete class error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET CLASS STATISTICS
# ===========================================
@classes_bp.route('/statistics', methods=['GET'])
@token_required
def get_class_statistics():
    """Get statistics for all classes"""
    try:
        statistics = fetch_all("""
            SELECT 
                k.id,
                k.nama_kelas,
                k.tingkat,
                j.kode as jurusan_kode,
                j.nama as jurusan_nama,
                g.nama as wali_kelas_nama,
                COUNT(s.id) as jumlah_siswa,
                SUM(CASE WHEN s.gender = 'L' THEN 1 ELSE 0 END) as laki_laki,
                SUM(CASE WHEN s.gender = 'P' THEN 1 ELSE 0 END) as perempuan
            FROM kelas k
            LEFT JOIN jurusan j ON k.jurusan_id = j.id
            LEFT JOIN guru g ON k.wali_kelas_id = g.id
            LEFT JOIN siswa s ON k.id = s.kelas_id
            GROUP BY k.id, k.nama_kelas, k.tingkat, j.kode, j.nama, g.nama
            ORDER BY k.tingkat, j.kode, k.nama_kelas
        """)

        # Calculate totals
        total_kelas = len(statistics)
        total_siswa = sum(s['jumlah_siswa'] or 0 for s in statistics)
        total_laki = sum(s['laki_laki'] or 0 for s in statistics)
        total_perempuan = sum(s['perempuan'] or 0 for s in statistics)

        # Add tingkat label
        for stat in statistics:
            stat['tingkat_label'] = get_tingkat_label(stat['tingkat'])

        return jsonify({
            "success": True,
            "total_kelas": total_kelas,
            "total_siswa": total_siswa,
            "total_laki_laki": total_laki,
            "total_perempuan": total_perempuan,
            "rata_rata_per_kelas": round(total_siswa / total_kelas, 1) if total_kelas > 0 else 0,
            "data": statistics
        })

    except Exception as e:
        logger.error(f"Get class statistics error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ===========================================
# GET STUDENTS IN CLASS
# ===========================================
@classes_bp.route('/<int:id>/siswa', methods=['GET'])
@token_required
def get_students_in_class(id):
    """Get all students in a specific class"""
    try:
        # Check if class exists
        kelas = fetch_one("SELECT id, nama_kelas FROM kelas WHERE id = %s", (id,))
        if not kelas:
            return jsonify({
                "success": False,
                "message": f"Kelas dengan ID {id} tidak ditemukan"
            }), 404

        # Get students
        students = fetch_all("""
            SELECT 
                id, nis, nisn, nama, gender, card_version
            FROM siswa 
            WHERE kelas_id = %s
            ORDER BY nama
        """, (id,))

        # Add gender labels
        for student in students:
            student['gender_label'] = (
                'Laki-laki' if student['gender'] == 'L' 
                else 'Perempuan' if student['gender'] == 'P' 
                else '-'
            )

        return jsonify({
            "success": True,
            "kelas": {
                "id": kelas['id'],
                "nama_kelas": kelas['nama_kelas']
            },
            "total_siswa": len(students),
            "data": students
        })

    except Exception as e:
        logger.error(f"Get students in class error: {e}")
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
