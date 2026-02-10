const API_URL = "http://localhost:8080/api";

/* ===============================
   TOKEN MANAGEMENT
================================ */

function getToken() {
    return localStorage.getItem("token");
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "login.html";
}

/* ===============================
   FETCH WRAPPER (JWT AWARE)
================================ */

function apiFetch(endpoint, options = {}) {
    const token = getToken();

    return fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            ...(options.headers || {})
        }
    }).then(res => {
        if (res.status === 401) {
            alert("Session habis. Silakan login ulang.");
            logout();
            throw new Error("Unauthorized");
        }
        return res.json();
    });
}

/* ===============================
   LOAD STUDENTS
================================ */

document.addEventListener("DOMContentLoaded", () => {
    if (!getToken()) {
        window.location.href = "login.html";
        return;
    }
    loadStudents();
});

function loadStudents() {
    apiFetch("/students")
        .then(data => {
            if (!data.success) {
                alert(data.message || "Gagal memuat data");
                return;
            }

            const table = document.getElementById("studentTable");
            table.innerHTML = "";

            data.students.forEach(siswa => {
                table.innerHTML += `
                    <tr>
                        <td>${siswa.nis}</td>
                        <td>${siswa.nama}</td>
                        <td>${siswa.kelas}</td>
                        <td>
                            <button onclick="editStudent(
                                '${siswa.nis}',
                                '${siswa.nama}',
                                '${siswa.kelas}'
                            )">Edit</button>
                            <button onclick="deleteStudent('${siswa.nis}')">Hapus</button>
                        </td>
                    </tr>
                `;
            });
        })
        .catch(err => console.error(err));
}

/* ===============================
   FORM SUBMIT (CREATE & UPDATE)
================================ */

document
    .getElementById("studentForm")
    .addEventListener("submit", submitForm);

function submitForm(e) {
    e.preventDefault();

    const oldNis = document.getElementById("oldNis").value;
    const nis = document.getElementById("nis").value.trim();
    const nama = document.getElementById("nama").value.trim();
    const kelas = document.getElementById("kelas").value.trim();

    if (!nis || !nama || !kelas) {
        alert("Lengkapi semua data");
        return;
    }

    const payload = { nis, nama, kelas };

    if (oldNis) {
        // UPDATE
        apiFetch(`/students/${oldNis}`, {
            method: "PUT",
            body: JSON.stringify(payload)
        })
        .then(handleResponse);
    } else {
        // CREATE
        apiFetch("/students/add", {
            method: "POST",
            body: JSON.stringify(payload)
        })
        .then(handleResponse);
    }
}

function handleResponse(data) {
    if (!data.success) {
        alert(data.message || "Operasi gagal");
        return;
    }

    resetForm();
    loadStudents();
}

/* ===============================
   EDIT
================================ */

function editStudent(nis, nama, kelas) {
    document.getElementById("oldNis").value = nis;
    document.getElementById("nis").value = nis;
    document.getElementById("nis").disabled = true;
    document.getElementById("nama").value = nama;
    document.getElementById("kelas").value = kelas;
}

/* ===============================
   DELETE
================================ */

function deleteStudent(nis) {
    if (!confirm("Hapus siswa ini?")) return;

    apiFetch(`/students/${nis}`, {
        method: "DELETE"
    })
    .then(data => {
        if (!data.success) {
            alert(data.message || "Gagal menghapus siswa");
            return;
        }
        loadStudents();
    });
}

/* ===============================
   RESET FORM
================================ */

function resetForm() {
    document.getElementById("studentForm").reset();
    document.getElementById("oldNis").value = "";
    document.getElementById("nis").disabled = false;
}
