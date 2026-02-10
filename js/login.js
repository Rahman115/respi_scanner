const API_URL = "http://localhost:8080/api";

document
    .getElementById("loginForm")
    .addEventListener("submit", login);

function login(e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
        alert("Username dan password wajib diisi");
        return;
    }

    fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert(data.message || "Login gagal");
            return;
        }

        // SIMPAN JWT
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));

        // PINDAH KE HALAMAN CRUD
        window.location.href = "index.html";
    })
    .catch(err => {
        console.error(err);
        alert("Gagal menghubungi server");
    });
}
