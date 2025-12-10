/**
 * Auth Module - Manejo de autenticación
 */

const AUTH_CONFIG = {
    API_URL: 'http://localhost:5000/api',
    TOKEN_KEY: 'iot_token',
    USER_KEY: 'iot_user'
};

// Obtener token almacenado
function getToken() {
    return localStorage.getItem(AUTH_CONFIG.TOKEN_KEY);
}

// Guardar token
function saveToken(token) {
    localStorage.setItem(AUTH_CONFIG.TOKEN_KEY, token);
}

// Eliminar token
function removeToken() {
    localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY);
    localStorage.removeItem(AUTH_CONFIG.USER_KEY);
}

// Guardar datos de usuario
function saveUser(user) {
    localStorage.setItem(AUTH_CONFIG.USER_KEY, JSON.stringify(user));
}

// Obtener datos de usuario
function getUser() {
    const userData = localStorage.getItem(AUTH_CONFIG.USER_KEY);
    return userData ? JSON.parse(userData) : null;
}

// Verificar si está autenticado
function isAuthenticated() {
    return getToken() !== null;
}

// Login
async function login(username, password) {
    try {
        const response = await fetch(`${AUTH_CONFIG.API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error en login');
        }

        // Guardar token y usuario
        saveToken(data.token);
        saveUser(data.user);

        return data;
    } catch (error) {
        console.error('Error en login:', error);
        throw error;
    }
}

// Logout
function logout() {
    removeToken();
    showScreen('loginScreen');
}

// Verificar token
async function verifyToken() {
    const token = getToken();
    
    if (!token) {
        return false;
    }

    try {
        const response = await fetch(`${AUTH_CONFIG.API_URL}/auth/verify`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        return response.ok;
    } catch (error) {
        console.error('Error verificando token:', error);
        return false;
    }
}

// Obtener headers con autenticación
function getAuthHeaders() {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Manejar respuesta no autorizada
function handleUnauthorized() {
    removeToken();
    showScreen('loginScreen');
    showError('Sesión expirada. Por favor inicie sesión nuevamente.');
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const logoutBtn = document.getElementById('logoutBtn');

    // Form de login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorEl = document.getElementById('loginError');

            try {
                errorEl.classList.remove('show');
                errorEl.textContent = '';

                const result = await login(username, password);

                // Login exitoso
                console.log('Login exitoso:', result.user);
                
                // Mostrar dashboard
                showScreen('dashboardScreen');
                initDashboard();

            } catch (error) {
                errorEl.textContent = error.message;
                errorEl.classList.add('show');
            }
        });
    }

    // Botón de logout
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Verificar autenticación al cargar
    checkAuth();
});

// Verificar autenticación
async function checkAuth() {
    if (isAuthenticated()) {
        const valid = await verifyToken();
        
        if (valid) {
            showScreen('dashboardScreen');
            initDashboard();
        } else {
            logout();
        }
    } else {
        showScreen('loginScreen');
    }
}

// Mostrar pantalla
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    const screen = document.getElementById(screenId);
    if (screen) {
        screen.classList.add('active');
    }
}

// Mostrar error
function showError(message) {
    const errorEl = document.getElementById('loginError');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.add('show');
        
        setTimeout(() => {
            errorEl.classList.remove('show');
        }, 5000);
    }
}