const API_URL = 'http://127.0.0.1:8000';

async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        window.location.href = '/shared/login.html';
        return;
    }

    return response;
}

function initAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/shared/login.html';
        return;
    }

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const role = (payload.role || '').toLowerCase();
        const currentPath = window.location.pathname;

        if (currentPath.includes('/admin/') && role !== 'admin') {
            window.location.href = '/employee/dashboard.html';
        } else if (currentPath.includes('/support/') && role !== 'agent' && role !== 'admin') {
            window.location.href = '/employee/dashboard.html';
        } else if (currentPath.includes('/employee/') && role !== 'employee' && role !== 'agent' && role !== 'admin') {
            window.location.href = '/shared/login.html';
        }

        const userDisplayName = payload.full_name || payload.username || payload.sub || 'User';
        const nameEl = document.getElementById('user-name');
        if (nameEl) nameEl.textContent = userDisplayName;

        const roleEl = document.getElementById('user-role');
        if (roleEl) roleEl.textContent = role;

        const initialsEl = document.getElementById('user-initials');
        if (initialsEl) initialsEl.textContent = userDisplayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

        document.getElementById('logout-btn')?.addEventListener('click', () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            window.location.href = '/shared/login.html';
        });

        document.getElementById('notifications-btn')?.addEventListener('click', () => {
            window.location.href = '/employee/notifications.html';
        });
    } catch (e) {
        localStorage.removeItem('access_token');
        window.location.href = '/shared/login.html';
    }
}

async function loadNotifications() {
    try {
        const response = await apiRequest('/api/notifications?unread_only=true');
        if (response.ok) {
            const data = await response.json();
            const badge = document.getElementById('notification-badge');
            if (badge) {
                badge.textContent = data.total > 9 ? '9+' : data.total;
                badge.classList.toggle('hidden', data.total === 0);
            }
        }
    } catch (e) {
        console.error('Failed to load notifications:', e);
    }
}

setInterval(loadNotifications, 30000);
loadNotifications();