/**
 * Dashboard Module - Gestión del dashboard principal
 */

// Inicializar dashboard
function initDashboard() {
    const user = getUser();
    
    if (!user) {
        logout();
        return;
    }

    // Mostrar información del usuario
    document.getElementById('userName').textContent = user.full_name;
    document.getElementById('userRole').textContent = getRoleLabel(user.role);

    // Mostrar/ocultar secciones según rol
    if (user.role.includes('admin')) {
        document.querySelectorAll('.admin-only').forEach(el => {
            el.classList.add('show');
            el.style.display = 'block';
        });
    }

    // Cargar resumen inicial
    loadOverview();

    // Configurar tabs
    setupTabs();

    // Configurar WebSocket
    // setupWebSocket();

    // Auto-actualización cada 30 segundos
    setInterval(() => {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'overview') {
            loadOverview();
        }
    }, 30000);
}

// Obtener etiqueta de rol
function getRoleLabel(role) {
    const roleMap = {
        'ejecutivo_alcalde': 'Alcalde',
        'ejecutivo_director': 'Director',
        'operativo_admin': 'Administrador',
        'operativo_user': 'Usuario'
    };
    return roleMap[role] || 'Usuario';
}

// Configurar tabs
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Actualizar botones
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Actualizar contenido
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            const targetContent = document.getElementById(tabId);
            if (targetContent) {
                targetContent.classList.add('active');
                
                // Cargar datos según tab
                switch(tabId) {
                    case 'overview':
                        loadOverview();
                        break;
                    case 'aire':
                        loadSensorData('aire');
                        break;
                    case 'sonido':
                        loadSensorData('sonido');
                        break;
                    case 'soterrado':
                        loadSensorData('soterrado');
                        break;
                }
            }
        });
    });
}

// Cargar resumen
async function loadOverview() {
    try {
        const response = await fetch(`${AUTH_CONFIG.API_URL}/sensors/summary`, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            handleUnauthorized();
            return;
        }

        const data = await response.json();

        // Actualizar contadores
        let totalCount = 0;
        
        if (data.aire) {
            document.getElementById('aireCount').textContent = data.aire.total_records.toLocaleString();
            totalCount += data.aire.total_records;
        }
        
        if (data.sonido) {
            document.getElementById('sonidoCount').textContent = data.sonido.total_records.toLocaleString();
            totalCount += data.sonido.total_records;
        }
        
        if (data.soterrado) {
            document.getElementById('soterradoCount').textContent = data.soterrado.total_records.toLocaleString();
            totalCount += data.soterrado.total_records;
        }
        
        document.getElementById('totalCount').textContent = totalCount.toLocaleString();

        // Cargar gráficos de resumen
        await loadOverviewCharts();

    } catch (error) {
        console.error('Error cargando resumen:', error);
    }
}

// Cargar gráficos de resumen
async function loadOverviewCharts() {
    // Cargar últimas lecturas de aire
    try {
        const aireResponse = await fetch(`${AUTH_CONFIG.API_URL}/sensors/aire/latest?limit=50`, {
            headers: getAuthHeaders()
        });
        
        if (aireResponse.ok) {
            const aireData = await aireResponse.json();
            createOverviewChart('overviewCO2Chart', aireData.data, 'object.co2', 'CO2 (ppm)', '#3b82f6');
        }
    } catch (error) {
        console.error('Error cargando datos de aire:', error);
    }

    // Cargar últimas lecturas de sonido
    try {
        const sonidoResponse = await fetch(`${AUTH_CONFIG.API_URL}/sensors/sonido/latest?limit=50`, {
            headers: getAuthHeaders()
        });
        
        if (sonidoResponse.ok) {
            const sonidoData = await sonidoResponse.json();
            createOverviewChart('overviewSonidoChart', sonidoData.data, 'object.LAeq', 'LAeq (dB)', '#f59e0b');
        }
    } catch (error) {
        console.error('Error cargando datos de sonido:', error);
    }
}

// Crear gráfico de resumen
function createOverviewChart(canvasId, data, field, label, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Destruir gráfico existente
    if (window.charts && window.charts[canvasId]) {
        window.charts[canvasId].destroy();
    }

    // Preparar datos
    const values = data.slice(0, 50).reverse().map(d => parseFloat(d[field]) || 0);
    const labels = data.slice(0, 50).reverse().map((d, i) => i + 1);

    // Crear gráfico
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: values,
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });

    // Guardar referencia
    if (!window.charts) window.charts = {};
    window.charts[canvasId] = chart;
}

// Cargar datos de sensor específico
async function loadSensorData(sensorType) {
    const limitSelect = document.getElementById(`${sensorType}Limit`);
    const limit = limitSelect ? limitSelect.value : 100;

    try {
        const response = await fetch(`${AUTH_CONFIG.API_URL}/sensors/${sensorType}/latest?limit=${limit}`, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            handleUnauthorized();
            return;
        }

        const data = await response.json();

        // Renderizar gráficos según tipo de sensor
        switch(sensorType) {
            case 'aire':
                renderAireCharts(data.data);
                break;
            case 'sonido':
                renderSonidoCharts(data.data);
                break;
            case 'soterrado':
                renderSoterradoCharts(data.data);
                break;
        }

    } catch (error) {
        console.error(`Error cargando datos de ${sensorType}:`, error);
    }
}

// Renderizar gráficos de aire
function renderAireCharts(data) {
    const reversedData = data.slice().reverse();
    
    createSensorChart('aireCO2Chart', reversedData, 'object.co2', 'CO2 (ppm)', '#3b82f6');
    createSensorChart('aireTempChart', reversedData, 'object.temperature', 'Temperatura (°C)', '#ef4444');
    createSensorChart('aireHumChart', reversedData, 'object.humidity', 'Humedad (%)', '#10b981');
    createSensorChart('airePresChart', reversedData, 'object.pressure', 'Presión (hPa)', '#8b5cf6');
}

// Renderizar gráficos de sonido
function renderSonidoCharts(data) {
    const reversedData = data.slice().reverse();
    
    createSensorChart('sonidoLAeqChart', reversedData, 'object.LAeq', 'LAeq (dB)', '#f59e0b');
    createSensorChart('sonidoLAIChart', reversedData, 'object.LAI', 'LAI (dB)', '#06b6d4');
    createSensorChart('sonidoLAImaxChart', reversedData, 'object.LAImax', 'LAImax (dB)', '#ec4899');
}

// Renderizar gráficos de soterrado
function renderSoterradoCharts(data) {
    const reversedData = data.slice().reverse();
    
    createSensorChart('soterradoDistChart', reversedData, 'object.distance', 'Distancia (cm)', '#6366f1');
}

// WebSocket setup (opcional)
function setupWebSocket() {
    // Implementar si se necesita actualización en tiempo real
    console.log('WebSocket setup - TODO');
}