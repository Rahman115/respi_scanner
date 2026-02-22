// path ../js/navbar.js
const sidebarMenu = [
  {
    title: "Dashboard",
    icon: "fas fa-home",
    path: "index.html",
    roles: ["admin", "guru"]
  },
  {
    title: "Verifikasi QR",
    icon: "fas fa-check-circle",
    path: "absensi/verify-qr.html",
    roles: ["admin", "guru"]
  },
  {
    title: "Bulk Generate",
    icon: "fas fa-layer-group",
    path: "absensi/bulk-generate.html",
    roles: ["admin"]
  },
  {
    title: "Cek NISN",
    icon: "fas fa-search",
    path: "absensi/check-nisn.html",
    roles: ["admin", "guru"]
  },
  {
    title: "Scan Legacy",
    icon: "fas fa-qrcode",
    path: "absensi/scan-legacy.html",
    roles: ["admin", "guru"]
  },

  // ===== MENU SISWA =====
  {
    title: "Mode Siswa",
    icon: "fas fa-user-graduate",
    path: "siswa/resiswa.html",
    roles: ["admin", "guru"]
  },
  {
    title: "Kartu Siswa",
    icon: "fas fa-id-card",
    path: "siswa/recard.html",
    roles: ["admin"]
  },
  {
    title: "Verifikasi Siswa",
    icon: "fas fa-user-check",
    path: "siswa/verify.html",
    roles: ["admin", "guru"]
  },

  // ===== MENU LAPORAN =====
  {
    title: "Attendance Dashboard",
    icon: "fas fa-chart-bar",
    path: "laporan/attendance_dashboard.html",
    roles: ["admin", "guru"]
  },
  {
    title: "Today Attendance",
    icon: "fas fa-calendar-day",
    path: "laporan/today_attendance.html",
    roles: ["admin", "guru", "siswa"]
  }
];

function renderSidebar(role) {
  const menuContainer = document.querySelector(".sidebar-menu");
  menuContainer.innerHTML = "";
  
  const API_URL = window.location.origin;
  console.log('API_URL:', API_URL);

  sidebarMenu
    .filter(item => item.roles.includes(role))
    .forEach(item => {
      const li = document.createElement("li");
      li.classList.add("menu-item");

      li.innerHTML = `
        <a href="${API_URL}/${item.path}">
          <i class="${item.icon}"></i>
          <span>${item.title}</span>
        </a>
      `;

      menuContainer.appendChild(li);
    });
}
