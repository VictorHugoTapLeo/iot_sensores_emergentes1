/**
 * Charts Module - Gestión de gráficos con Chart.js
 */

// Almacenar instancias de gráficos
window.charts = {};

/**
 * Crear gráfico genérico de sensor
 */
function createSensorChart(canvasId, data, field, label, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`Canvas ${canvasId} no encontrado`);
        return;
    }

    const ctx = canvas.getContext('2d');

    // Destruir gráfico existente
    if (window.charts[canvasId]) {
        window.charts[canvasId].destroy();
    }

    // Preparar datos
    const values = data.map(d => parseFloat(d[field]) || 0);
    const labels = data.map((d, i) => {
        // Usar timestamp si está disponible
        if (d.time) {
            const date = new Date(d.time);
            return date.toLocaleTimeString('es-ES', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
        return i + 1;
    });

    // Calcular estadísticas
    const stats = calculateStats(values);

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
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y.toFixed(2);
                            return label;
                        },
                        footer: function() {
                            return [
                                `Promedio: ${stats.mean.toFixed(2)}`,
                                `Min: ${stats.min.toFixed(2)} | Max: ${stats.max.toFixed(2)}`
                            ];
                        }
                    }
                },
                title: {
                    display: true,
                    text: `${label} - Últimas lecturas`,
                    font: {
                        size: 14
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Tiempo'
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        autoSkip: true
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: label
                    },
                    beginAtZero: false
                }
            }
        }
    });

    // Guardar referencia
    window.charts[canvasId] = chart;

    return chart;
}

/**
 * Crear gráfico de predicciones
 */
function createPredictionChart(canvasId, historicalData, predictionData, field, label, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`Canvas ${canvasId} no encontrado`);
        return;
    }

    const ctx = canvas.getContext('2d');

    // Destruir gráfico existente
    if (window.charts[canvasId]) {
        window.charts[canvasId].destroy();
    }

    // Preparar datos históricos
    const historicalValues = historicalData.map(d => parseFloat(d[field]) || 0);
    const historicalLabels = historicalData.map((d, i) => {
        if (d.time) {
            const date = new Date(d.time);
            return date.toLocaleDateString('es-ES', { 
                month: 'short', 
                day: 'numeric' 
            });
        }
        return `H-${i}`;
    });

    // Preparar datos de predicción
    const predictionValues = predictionData.predictions[field] || [];
    const predictionLabels = predictionData.timestamps.map(ts => {
        const date = new Date(ts);
        return date.toLocaleDateString('es-ES', { 
            month: 'short', 
            day: 'numeric' 
        });
    });

    // Combinar labels
    const allLabels = [...historicalLabels, ...predictionLabels];

    // Crear datasets
    const datasets = [
        {
            label: 'Datos Históricos',
            data: [...historicalValues, ...Array(predictionValues.length).fill(null)],
            borderColor: color,
            backgroundColor: color + '40',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 3
        },
        {
            label: 'Predicción ML',
            data: [...Array(historicalValues.length).fill(null), ...predictionValues],
            borderColor: '#f59e0b',
            backgroundColor: '#f59e0b20',
            borderWidth: 2,
            borderDash: [5, 5],
            fill: true,
            tension: 0.4,
            pointRadius: 3
        }
    ];

    // Crear gráfico
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: true,
                    text: `${label} - Histórico vs Predicción`,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Fecha'
                    },
                    ticks: {
                        maxTicksLimit: 15,
                        autoSkip: true
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: label
                    },
                    beginAtZero: false
                }
            }
        }
    });

    // Guardar referencia
    window.charts[canvasId] = chart;

    return chart;
}

/**
 * Calcular estadísticas básicas
 */
function calculateStats(values) {
    const validValues = values.filter(v => !isNaN(v) && v !== null);
    
    if (validValues.length === 0) {
        return { mean: 0, min: 0, max: 0, std: 0 };
    }

    const sum = validValues.reduce((a, b) => a + b, 0);
    const mean = sum / validValues.length;
    const min = Math.min(...validValues);
    const max = Math.max(...validValues);
    
    // Desviación estándar
    const squareDiffs = validValues.map(v => Math.pow(v - mean, 2));
    const avgSquareDiff = squareDiffs.reduce((a, b) => a + b, 0) / validValues.length;
    const std = Math.sqrt(avgSquareDiff);

    return { mean, min, max, std };
}

/**
 * Destruir todos los gráficos
 */
function destroyAllCharts() {
    Object.keys(window.charts).forEach(key => {
        if (window.charts[key]) {
            window.charts[key].destroy();
            delete window.charts[key];
        }
    });
}