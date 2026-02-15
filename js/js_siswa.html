// js/js_siswa.js - JavaScript untuk halaman manajemen siswa

// State management
let allStudents = [];
let filteredStudents = [];
let currentPage = 1;
const itemsPerPage = 10;

// Load students on page load
document.addEventListener('DOMContentLoaded', function() {
    loadStudents();
    loadKelasFilter();
    setupInputValidation();
});

// ===========================================
// LOAD DATA
// ===========================================

async function loadStudents() {
    showLoading('Memuat data siswa...');
    
    try {
        const response = await makeRequest('/students', 'GET');
        
        if (response.success) {
            allStudents = response.students || [];
            updateStats();
            applyFilters();
        } else {
            showNotification(response.message, 'error');
        }
    } catch (error) {
        showNotification('Gagal memuat data: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function updateStats() {
    const total = allStudents.length;
    const denganNISN = allStudents.filter(s => s.nisn && s.nisn.length === 10).length;
    const tanpaNISN = total - denganNISN;
    
    document.getElementById('totalSiswa').textContent = total;
    document.getElementById('denganNISN').textContent = denganNISN;
    document.getElementById('tanpaNISN').textContent = tanpaNISN;
    document.getElementById('qrTersedia').textContent = denganNISN; // QR tersedia untuk yang punya NISN
}

function loadKelasFilter() {
    const kelas = [...new Set(allStudents.map(s => s.kelas))];
    const select = document.getElementById('filterKelas');
    select.innerHTML = '<option value="">Semua Kelas</option>' + 
        kelas.map(k => `<option value="${k}">${k}</option>`).join('');
}

// ===========================================
// FILTER FUNCTIONS
// ===========================================

function applyFilters() {
    const kelas = document.getElementById('filterKelas').value;
    const nisnFilter = document.getElementById('filterNISN').value;
    const search = document.getElementById('searchInput').value.toLowerCase();

    filteredStudents = allStudents.filter(s => {
        // Filter kelas
        if (kelas && s.kelas !== kelas) return false;
        
        // Filter NISN
        if (nisnFilter === 'with' && !s.nisn) return false;
        if (nisnFilter === 'without' && s.nisn) return false;
        
        // Filter search
        if (search) {
            return s.nis.toLowerCase().includes(search) ||
                   (s.nisn && s.nisn.toLowerCase().includes(search)) ||
                   s.nama.toLowerCase().includes(search) ||
                   s.kelas.toLowerCase().includes(search);
        }
        
        return true;
    });

    document.getElementById('dataCount').textContent = `${filteredStudents.length} data`;
    currentPage = 1;
    renderTable();
}

function resetFilters() {
    document.getElementById('filterKelas').value = '';
    document.getElementById('filterNISN').value = '';
    document.getElementById('searchInput').value = '';
    applyFilters();
}

// ===========================================
// TABLE RENDERING
// ===========================================

function renderTable() {
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageData = filteredStudents.slice(start, end);
    
    const tbody = document.getElementById('studentTableBody');
    
    if (pageData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Tidak ada data siswa</td></tr>';
    } else {
        tbody.innerHTML = pageData.map((s, index) => {
            const statusClass = s.nisn ? 'status-valid' : 'status-missing';
            const statusText = s.nisn ? 'Valid' : 'Tidak Ada';
            const nisnDisplay = s.nisn || '-';
            
            return `
                <tr>
                    <td>${start + index + 1}</td>
                    <td><strong>${s.nis}</strong></td>
                    <td class="nisn-column">${nisnDisplay}</td>
                    <td>${s.nama}</td>
                    <td>${s.kelas}</td>
                    <td>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </td>
                    <td>
                        ${s.nisn ? 
                            `<button class="btn-icon btn-qr btn-small" onclick="showQR('${s.nis}')" title="Lihat QR">
                                <i class="fas fa-qrcode"></i>
                            </button>` : 
                            `<span class="status-badge status-missing">-</span>`}
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-icon btn-view btn-small" onclick="showDetail('${s.nis}')" title="Detail">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn-icon btn-edit btn-small" onclick="editStudent('${s.nis}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-icon btn-delete btn-small" onclick="deleteStudent('${s.nis}')" title="Hapus">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    updatePagination();
}

function updatePagination() {
    const totalPages = Math.ceil(filteredStudents.length / itemsPerPage);
    document.getElementById('pageInfo').textContent = `Halaman ${currentPage} dari ${totalPages || 1}`;
    
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages || totalPages === 0;
}

function changePage(direction) {
    const totalPages = Math.ceil(filteredStudents.length / itemsPerPage);
    
    if (direction === 'prev' && currentPage > 1) {
        currentPage--;
    } else if (direction === 'next' && currentPage < totalPages) {
        currentPage++;
    }
    renderTable();
}

// ===========================================
// FORM FUNCTIONS
// ===========================================

function setupInputValidation() {
    const nisnInput = document.getElementById('nisn');
    
    nisnInput.addEventListener('input', function() {
        this.value = this.value.replace(/\D/g, ''); // Hanya angka
        if (this.value.length > 10) {
            this.value = this.value.slice(0, 10);
        }
    });
    
    // Form submit handler
    document.getElementById('studentForm').addEventListener('submit', handleFormSubmit);
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const nis = document.getElementById('nis').value.trim();
    const nisn = document.getElementById('nisn').value.trim();
    const nama = document.getElementById('nama').value.trim();
    const kelas = document.getElementById('kelas').value.trim();
    const oldNis = document.getElementById('oldNis').value;

    // Validasi
    if (!nis || !nama || !kelas) {
        showNotification('Semua field harus diisi', 'error');
        return;
    }

    // Validasi NISN jika diisi
    if (nisn && !/^\d{10}$/.test(nisn)) {
        showNotification('NISN harus 10 digit angka', 'error');
        return;
    }

    const studentData = { nis, nisn, nama, kelas };
    
    try {
        let response;
        
        if (oldNis) {
            // Update
            response = await makeRequest(`/students/${oldNis}`, 'PUT', studentData);
            if (response.success) {
                showNotification('Data siswa berhasil diperbarui', 'success');
            }
        } else {
            // Create
            response = await makeRequest('/students/add', 'POST', studentData);
            if (response.success) {
                showNotification('Siswa berhasil ditambahkan', 'success');
            }
        }

        if (response.success) {
            resetForm();
            await loadStudents();
        } else {
            showNotification(response.message, 'error');
        }
    } catch (error) {
        showNotification('Gagal menyimpan data: ' + error.message, 'error');
    }
}

function resetForm() {
    document.getElementById('studentForm').reset();
    document.getElementById('oldNis').value = '';
    document.getElementById('formTitle').innerHTML = '<i class="fas fa-user-plus"></i> Tambah Siswa Baru';
    document.getElementById('submitBtn').innerHTML = '<i class="fas fa-save"></i> Simpan';
    
    // Reset to default
    document.getElementById('nis').disabled = false;
    document.getElementById('nis').focus();
}

async function editStudent(nis) {
    try {
        const student = allStudents.find(s => s.nis === nis);
        
        if (student) {
            document.getElementById('oldNis').value = student.nis;
            document.getElementById('nis').value = student.nis;
            document.getElementById('nisn').value = student.nisn || '';
            document.getElementById('nama').value = student.nama;
            document.getElementById('kelas').value = student.kelas;
            
            document.getElementById('formTitle').innerHTML = '<i class="fas fa-edit"></i> Edit Siswa';
            document.getElementById('submitBtn').innerHTML = '<i class="fas fa-save"></i> Update';
            
            // Disable NIS jika sedang edit
            document.getElementById('nis').disabled = true;
            
            // Scroll ke form
            document.querySelector('.feature-card').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    } catch (error) {
        showNotification('Gagal memuat data siswa', 'error');
    }
}

async function deleteStudent(nis) {
    const confirm = await showConfirm('Apakah Anda yakin ingin menghapus siswa ini?');
    
    if (confirm) {
        try {
            const response = await makeRequest(`/students/${nis}`, 'DELETE');
            
            if (response.success) {
                showNotification(response.message, 'success');
                await loadStudents();
                
                // Reset form jika yang dihapus sedang diedit
                if (document.getElementById('oldNis').value === nis) {
                    resetForm();
                }
            } else {
                showNotification(response.message, 'error');
            }
        } catch (error) {
            showNotification('Gagal menghapus data: ' + error.message, 'error');
        }
    }
}

// ===========================================
// DETAIL FUNCTIONS (akan di-override oleh HTML)
// ===========================================

// Fungsi ini akan di-override oleh script di HTML
window.showDetail = function(nis) {
    const student = allStudents.find(s => s.nis === nis);
    if (student) {
        alert(`Detail Siswa:\nNIS: ${student.nis}\nNISN: ${student.nisn || '-'}\nNama: ${student.nama}\nKelas: ${student.kelas}`);
    }
};

window.showQR = function(nis) {
    alert('Fitur QR akan segera hadir');
};

// ===========================================
// EXPORT FUNCTIONS
// ===========================================

window.loadStudents = loadStudents;
window.applyFilters = applyFilters;
window.resetFilters = resetFilters;
window.changePage = changePage;
window.resetForm = resetForm;
window.editStudent = editStudent;
window.deleteStudent = deleteStudent;
window.showDetail = showDetail;
window.showQR = showQR;
