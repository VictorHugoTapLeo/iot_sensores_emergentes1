/**
 * App Module - Punto de entrada principal de la aplicación
 */

// Configuración global
window.APP_CONFIG = {
    AUTO_REFRESH_INTERVAL: 30000, // 30 segundos
    CHART_COLORS: {
        primary: '#2563eb',
        secondary: '#64748b',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444'
    }
};

// Inicialización al cargar el DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando Sistema IoT GAMC');
    
    // Verificar autenticación
    checkAuth();
    
    // Configurar event listeners adicionales
    setupEventListeners();
    
    // Configurar manejo de errores global
    setupErrorHandling();
});

/**
 * Configurar event listeners adicionales
 */
function setupEventListeners() {
    // Escuchar cambios en los selects de límite
    ['aire', 'sonido', 'soterrado'].forEach(sensorType => {
        const selectEl = document.getElementById(`${sensorType}Limit`);
        if (selectEl) {
            selectEl.addEventListener('change', () => {
                loadSensorData(sensorType);
            });
        }
    });

    // Tecla ESC para cerrar modales (si hay)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            // Cerrar modales si existen
        }
    });

    // Detectar pérdida de conexión
    window.addEventListener('online', () => {
        showNotification('Conexión restaurada', 'success');
    });

    window.addEventListener('offline', () => {
        showNotification('Sin conexión a internet', 'warning');
    });
}

/**
 * Configurar manejo de errores global
 */
function setupErrorHandling() {
    window.addEventListener('error', (e) => {
        console.error('Error global:', e);
        // Podríamos enviar esto a un servicio de logging
    });

    window.addEventListener('unhandledrejection', (e) => {
        console.error('Promise no manejada:', e);
    });
}

/**
 * Mostrar notificación temporal
 */
function showNotification(message, type = 'info') {
    const colors = {
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#2563eb'
    };

    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${colors[type] || colors.info};
        color: white;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        max-width: 300px;
        font-weight: 600;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remover después de 3 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Agregar estilos de animación
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

/**
 * Formatear fecha para display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Formatear número con separador de miles
 */
function formatNumber(number, decimals = 2) {
    return Number(number).toLocaleString('es-ES', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Exportar datos a CSV (utilidad futura)
 */
function exportToCSV(data, filename) {
    if (!data || data.length === 0) {
        showNotification('No hay datos para exportar', 'warning');
        return;
    }

    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => row[header]).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showNotification('Datos exportados correctamente', 'success');
}

/**
 * Debounce function para optimizar eventos
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function para limitar frecuencia de eventos
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Exportar funciones útiles globalmente
window.showNotification = showNotification;
window.formatDate = formatDate;
window.formatNumber = formatNumber;
window.exportToCSV = exportToCSV;
window.debounce = debounce;
window.throttle = throttle;

console.log('✅ Sistema IoT GAMC cargado correctamente');