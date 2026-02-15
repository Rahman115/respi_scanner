// script.js - JavaScript bersama untuk semua halaman

// API Configuration
const API_BASE_URL = 'http://localhost:8080/api'; // Sesuaikan dengan URL API Anda

// JWT Token Management
let JWT_TOKEN = localStorage.getItem('token') || '';

// Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadUserInfo();
});

// ===========================================
// AUTHENTICATION FUNCTIONS
// ===========================================

function checkAuth() {
    const publicPages = ['login.html'];
    const currentPage = window.location.pathname.split('/').pop();

    if (!publicPages.includes(currentPage) && !JWT_TOKEN) {
        // Redirect to login if not authenticated
        window.location.href = 'login.html';
    }
}

function loadUserInfo() {
    if (JWT_TOKEN) {
        try {
            // Decode JWT to get user info
            // const payload = JSON.parse(atob(JWT_TOKEN.split('.')[1]));
            const payload = JSON.parse(localStorage.getItem("user") || "{}");
            document.getElementById('userName').textContent = payload.nama || 'Admin';
        } catch (e) {
            console.log('Could not decode token');
        }
    }
}

function login(username, password) {
    return makeRequest('/auth/login', 'POST', { username, password }, false);
}

function logout() {
    localStorage.removeItem('token');
    JWT_TOKEN = '';
    window.location.href = 'login.html';
}

// ===========================================
// API REQUEST FUNCTION
// ===========================================

async function makeRequest(endpoint, method = 'GET', data = null, requiresAuth = true) {
    const headers = {
        'Content-Type': 'application/json'
    };

    if (requiresAuth && JWT_TOKEN) {
        headers['Authorization'] = `Bearer ${JWT_TOKEN}`;
    }

    const options = {
        method: method,
        headers: headers
    };

    if (data) {
        options.body = JSON.stringify(data);
    }
    console.log('Data : ', data);
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();

        // Log activity
        logActivity(`${method} ${endpoint}`, result.success ? 'success' : 'error');

        return result;
    } catch (error) {
        console.error('API Error:', error);
        logActivity(`${method} ${endpoint} - Network Error`, 'error');
        return { success: false, message: `Koneksi error: ${error.message}` };
    }
}

// ===========================================
// NOTIFICATION FUNCTIONS
// ===========================================

function showNotification(message, type = 'info', duration = 3000) {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;

    let icon = '';
    switch(type) {
        case 'success': icon = '✅'; break;
        case 'error': icon = '❌'; break;
        default: icon = 'ℹ️';
    }

    notification.innerHTML = `
        <span class="notification-icon">${icon}</span>
        <span class="notification-message">${message}</span>
    `;

    document.body.appendChild(notification);

    // Auto remove
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

function showLoading(message = 'Memuat...') {
    const loading = document.createElement('div');
    loading.className = 'loading-overlay';
    loading.id = 'loadingOverlay';
    loading.innerHTML = `
        <div class="loading-spinner"></div>
        <p>${message}</p>
    `;
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.getElementById('loadingOverlay');
    if (loading) loading.remove();
}

// ===========================================
// ACTIVITY LOGGING
// ===========================================

function logActivity(message, type = 'info') {
    const logs = JSON.parse(localStorage.getItem('activity_logs') || '[]');

    logs.unshift({
        time: new Date().toLocaleTimeString(),
        message: message,
        type: type
    });

    // Keep only last 50 logs
    if (logs.length > 50) logs.pop();

    localStorage.setItem('activity_logs', JSON.stringify(logs));
}

// ===========================================
// CONFIRMATION DIALOG
// ===========================================

function showConfirm(message) {
    return new Promise((resolve) => {
        // Simple confirm using browser's confirm
        // Bisa diganti dengan custom modal jika diperlukan
        resolve(confirm(message));
    });
}

// ===========================================
// DATE FORMATTING
// ===========================================

function formatDate(date) {
    const d = new Date(date);
    return d.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
    });
}

function formatTime(date) {
    const d = new Date(date);
    return d.toLocaleTimeString('id-ID', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// ===========================================
// EXPORT FUNCTIONS
// ===========================================

function exportToCSV(data, filename) {
    const csv = data.map(row =>
        row.map(cell => {
            if (typeof cell === 'string' && cell.includes(',')) {
                return `"${cell}"`;
            }
            return cell;
        }).join(',')
    ).join('\n');

    downloadFile(csv, filename);
}

function downloadFile(content, filename) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// ===========================================
// VALIDATION FUNCTIONS
// ===========================================

function isValidNISN(nisn) {
    return /^\d{10}$/.test(nisn);
}

function isValidNIS(nis) {
    return nis && nis.length > 0;
}

// ===========================================
// STORAGE HELPERS
// ===========================================

function saveToStorage(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function getFromStorage(key, defaultValue = null) {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : defaultValue;
}

// ===========================================
// EXPORT FUNCTIONS TO WINDOW
// ===========================================

window.API_BASE_URL = API_BASE_URL;
window.JWT_TOKEN = JWT_TOKEN;
window.makeRequest = makeRequest;
window.showNotification = showNotification;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showConfirm = showConfirm;
window.logout = logout;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.isValidNISN = isValidNISN;
window.isValidNIS = isValidNIS;
window.exportToCSV = exportToCSV;
window.downloadFile = downloadFile;
window.saveToStorage = saveToStorage;
window.getFromStorage = getFromStorage;
