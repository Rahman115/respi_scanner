const API_URL = "http://localhost:8080/api";

document.addEventListener("DOMContentLoaded", loadStudents);
document.getElementById("studentForm").addEventListener("submit", submitForm);

function loadStudents() {
    fetch(`${API_URL}/students`)
        .then(res => res.json())
        .then(data => {
            const table = document.getElementById("studentTable");
            table.innerHTML = "";
            cosole.log(data);
            data.data.forEach(siswa => {
                table.innerHTML += `
                    <tr>
                        <td>${siswa.nis}</td>
                        <td>${siswa.nama}</td>
                        <td>${siswa.kelas}</td>
                        <td>
                            <button class="btn-edit" onclick="editStudent('${siswa.nis}','${siswa.nama}','${siswa.kelas}')">Edit</button>
                            <button class="btn-delete" onclick="deleteStudent('${siswa.nis}')">Hapus</button>
                        </td>
                    </tr>
                `;
            });
        });
}

function submitForm(e) {
    e.preventDefault();

    const oldNis = document.getElementById("oldNis").value;
    const nis = document.getElementById("nis").value;
    const nama = document.getElementById("nama").value;
    const kelas = document.getElementById("kelas").value;

    const payload = { nis, nama, kelas };

    if (oldNis) {
        // UPDATE
        fetch(`${API_URL}/student/${oldNis}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(resetAndReload);
    } else {
        // CREATE
        fetch(`${API_URL}/student`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(resetAndReload);
    }
}

function editStudent(nis, nama, kelas) {
    document.getElementById("oldNis").value = nis;
    document.getElementById("nis").value = nis;
    document.getElementById("nis").disabled = true;
    document.getElementById("nama").value = nama;
    document.getElementById("kelas").value = kelas;
}

function deleteStudent(nis) {
    if (!confirm("Hapus siswa ini?")) return;

    fetch(`${API_URL}/student/${nis}`, {
        method: "DELETE"
    }).then(loadStudents);
}

function resetForm() {
    document.getElementById("studentForm").reset();
    document.getElementById("oldNis").value = "";
    document.getElementById("nis").disabled = false;
}

function resetAndReload() {
    resetForm();
    loadStudents();
}
