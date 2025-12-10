/**
 * Predictions Module - Gestión de predicciones ML
 */

// Hacer funciones globales
window.generatePredictions = generatePredictions;
window.trainModels = trainModels;
window.loadLogs = loadLogs;

/**
 * Generar predicciones
 */
async function generatePredictions() {
    console.log('Generando predicciones...');
    const sensorType = document.getElementById('predSensorType').value;
    const days = parseInt(document.getElementById('predDays').value);
    const resultsContainer = document.getElementById('predictionResults');

    if (!resultsContainer) return;

    // Mostrar loading
    resultsContainer.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div style="font-size: 48px; animation: spin 1s linear infinite;">⏳</div>
            <p style="margin-top: 20px; color: #64748b;">
                Generando predicciones para ${days} días...<br>
                <strong>Esto puede tomar 10-30 segundos.</strong><br>
                <small>Por favor espere...</small>
            </p>
        </div>
    `;
    
    // Agregar animación de spin
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);

    try {
        // Generar predicciones
        const response = await fetch(`${AUTH_CONFIG.API_URL}/predictions/${sensorType}/predict`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                days: days,
                frequency: days === 7 ? 'H' : 'D'
            })
        });

        if (response.status === 401) {
            handleUnauthorized();
            return;
        }

        if (!response.ok) {
            throw new Error('Error generando predicciones');
        }

        const predictionData = await response.json();

        // Cargar datos históricos
        const historicalResponse = await fetch(
            `${AUTH_CONFIG.API_URL}/sensors/${sensorType}/latest?limit=${days === 7 ? 168 : 30}`,
            { headers: getAuthHeaders() }
        );

        const historicalData = await historicalResponse.json();

        // Mostrar resultados
        displayPredictions(sensorType, historicalData.data, predictionData);

    } catch (error) {
        console.error('Error generando predicciones:', error);
        resultsContainer.innerHTML = `
            <div class="prediction-card" style="text-align: center; padding: 40px;">
                <div style="font-size: 48px;">❌</div>
                <h3 style="color: #ef4444; margin-top: 20px;">Error generando predicciones</h3>
                <p style="color: #64748b; margin-top: 10px;">${error.message}</p>
                <div style="margin-top: 20px; padding: 15px; background: #fef2f2; border-radius: 8px; text-align: left;">
                    <p style="color: #991b1b; font-weight: 600; margin-bottom: 10px;">Posibles causas:</p>
                    <ul style="color: #7f1d1d; margin-left: 20px;">
                        <li>No hay datos suficientes en MongoDB (mínimo 50 registros)</li>
                        <li>Los modelos no están entrenados</li>
                        <li>Error de conexión con la API</li>
                    </ul>
                    <p style="color: #991b1b; margin-top: 15px; font-weight: 600;">Solución:</p>
                    <ol style="color: #7f1d1d; margin-left: 20px;">
                        <li>Verificar que hay datos: Ir a pestaña "${sensorType.toUpperCase()}"</li>
                        <li>Si no hay datos, cargar: <code>python -m src.data_ingestion.csv_producer</code></li>
                        <li>Entrenar modelos: Ir a pestaña "Administración" → Entrenar Modelos</li>
                    </ol>
                </div>
                <button onclick="generatePredictions()" class="btn btn-primary" style="margin-top: 20px;">
                    🔄 Reintentar
                </button>
            </div>
        `;
    }
}

/**
 * Mostrar predicciones
 */
function displayPredictions(sensorType, historicalData, predictionData) {
    const resultsContainer = document.getElementById('predictionResults');
    if (!resultsContainer) return;

    // Obtener campos según tipo de sensor
    const fieldConfigs = {
        'aire': [
            { field: 'object.co2', label: 'CO2 (ppm)', color: '#3b82f6' },
            { field: 'object.temperature', label: 'Temperatura (°C)', color: '#ef4444' },
            { field: 'object.humidity', label: 'Humedad (%)', color: '#10b981' },
            { field: 'object.pressure', label: 'Presión (hPa)', color: '#8b5cf6' }
        ],
        'sonido': [
            { field: 'object.LAeq', label: 'LAeq (dB)', color: '#f59e0b' },
            { field: 'object.LAI', label: 'LAI (dB)', color: '#06b6d4' },
            { field: 'object.LAImax', label: 'LAImax (dB)', color: '#ec4899' }
        ],
        'soterrado': [
            { field: 'object.distance', label: 'Distancia (cm)', color: '#6366f1' }
        ]
    };

    const fields = fieldConfigs[sensorType] || [];

    // Crear HTML
    let html = `
        <div class="prediction-card">
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 48px;">✅</div>
                <h3 style="color: #10b981; margin-top: 15px;">Predicciones Generadas Exitosamente</h3>
                <p style="color: #64748b; margin-top: 10px;">
                    Predicción de ${predictionData.metadata.prediction_days} días | 
                    ${predictionData.metadata.total_predictions} puntos de datos
                </p>
            </div>
        </div>
    `;

    // Crear contenedor para cada campo
    fields.forEach((config, index) => {
        const canvasId = `predChart_${sensorType}_${index}`;
        
        html += `
            <div class="prediction-card">
                <h3>${config.label}</h3>
                <canvas id="${canvasId}"></canvas>
                ${renderPredictionStats(predictionData.predictions[config.field], config.label)}
            </div>
        `;
    });

    resultsContainer.innerHTML = html;

    // Crear gráficos
    setTimeout(() => {
        fields.forEach((config, index) => {
            const canvasId = `predChart_${sensorType}_${index}`;
            createPredictionChart(
                canvasId,
                historicalData.slice().reverse(),
                predictionData,
                config.field,
                config.label,
                config.color
            );
        });
    }, 100);
}

/**
 * Renderizar estadísticas de predicción
 */
function renderPredictionStats(values, label) {
    if (!values || values.length === 0) {
        return '';
    }

    const stats = calculateStats(values);

    return `
        <div style="margin-top: 20px; padding: 15px; background: #f8fafc; border-radius: 8px;">
            <p style="font-weight: 600; margin-bottom: 10px; color: #334155;">
                Estadísticas de Predicción:
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                <div>
                    <p style="font-size: 12px; color: #64748b;">Promedio</p>
                    <p style="font-size: 18px; font-weight: 600; color: #2563eb;">
                        ${stats.mean.toFixed(2)}
                    </p>
                </div>
                <div>
                    <p style="font-size: 12px; color: #64748b;">Mínimo</p>
                    <p style="font-size: 18px; font-weight: 600; color: #10b981;">
                        ${stats.min.toFixed(2)}
                    </p>
                </div>
                <div>
                    <p style="font-size: 12px; color: #64748b;">Máximo</p>
                    <p style="font-size: 18px; font-weight: 600; color: #ef4444;">
                        ${stats.max.toFixed(2)}
                    </p>
                </div>
                <div>
                    <p style="font-size: 12px; color: #64748b;">Desv. Est.</p>
                    <p style="font-size: 18px; font-weight: 600; color: #8b5cf6;">
                        ${stats.std.toFixed(2)}
                    </p>
                </div>
            </div>
        </div>
    `;
}

/**
 * Entrenar modelos ML (solo admin)
 */
async function trainModels() {
    console.log('Entrenando modelos...');
    
    const sensorType = document.getElementById('trainSensorType').value;
    const days = parseInt(document.getElementById('trainDays').value);
    const resultsContainer = document.getElementById('trainingResults');

    if (!resultsContainer) {
        console.error('Contenedor trainingResults no encontrado');
        return;
    }

    // Confirmar acción
    const sensorText = sensorType === 'all' ? 'todos los sensores' : sensorType;
    if (!confirm(`¿Está seguro de entrenar el modelo para ${sensorText} con ${days} días de datos?\n\nEsto puede tardar varios minutos.`)) {
        return;
    }

    // Mostrar loading con más detalles
    resultsContainer.innerHTML = `
        <div style="margin-top: 20px; padding: 30px; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;">
            <div style="font-size: 48px; animation: spin 1s linear infinite;">🎓</div>
            <p style="margin-top: 15px; color: #64748b; font-size: 18px; font-weight: 600;">
                Entrenando modelos de Machine Learning...
            </p>
            <p style="color: #64748b; margin-top: 10px;">
                Sensor: <strong>${sensorText}</strong><br>
                Días de entrenamiento: <strong>${days}</strong>
            </p>
            <div style="margin-top: 20px; padding: 15px; background: #eff6ff; border-radius: 8px;">
                <p style="color: #1e40af; font-size: 14px;">
                    ⏱️ Tiempo estimado: 2-5 minutos<br>
                    🔄 El proceso está en segundo plano<br>
                    📊 Se calcularán métricas de precisión
                </p>
            </div>
            <p style="color: #94a3b8; margin-top: 15px; font-size: 12px;">
                Por favor no cierre esta ventana...
            </p>
        </div>
    `;

    try {
        let response;
        
        if (sensorType === 'all') {
            response = await fetch(`${AUTH_CONFIG.API_URL}/predictions/train/all`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ days: days })
            });
        } else {
            response = await fetch(`${AUTH_CONFIG.API_URL}/predictions/${sensorType}/train`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ days: days })
            });
        }

        if (response.status === 401) {
            handleUnauthorized();
            return;
        }

        if (response.status === 403) {
            resultsContainer.innerHTML = `
                <div style="margin-top: 20px; padding: 30px; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;">
                    <div style="font-size: 48px;">🔒</div>
                    <h3 style="color: #ef4444; margin-top: 15px;">Permisos insuficientes</h3>
                    <p style="color: #64748b;">Solo los administradores pueden entrenar modelos.</p>
                </div>
            `;
            return;
        }

        if (!response.ok) {
            throw new Error('Error entrenando modelos');
        }

        const result = await response.json();

        // Mostrar resultados con más detalle
        let metricsHTML = '';
        
        if (result.metrics) {
            metricsHTML = '<div style="margin-top: 20px;">';
            metricsHTML += '<h4 style="color: #1e40af; margin-bottom: 15px;">📊 Métricas del Modelo:</h4>';
            
            for (const [field, metrics] of Object.entries(result.metrics)) {
                const r2Score = (metrics.test_r2 * 100).toFixed(2);
                const r2Color = metrics.test_r2 >= 0.85 ? '#10b981' : metrics.test_r2 >= 0.70 ? '#f59e0b' : '#ef4444';
                
                metricsHTML += `
                    <div style="margin-bottom: 15px; padding: 15px; background: #f8fafc; border-radius: 8px; border-left: 4px solid ${r2Color};">
                        <p style="font-weight: 600; color: #1e293b; margin-bottom: 8px;">${field}</p>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                            <div>
                                <p style="font-size: 12px; color: #64748b;">R² Score</p>
                                <p style="font-size: 18px; font-weight: 600; color: ${r2Color};">${r2Score}%</p>
                            </div>
                            <div>
                                <p style="font-size: 12px; color: #64748b;">RMSE</p>
                                <p style="font-size: 18px; font-weight: 600; color: #64748b;">${metrics.test_rmse.toFixed(2)}</p>
                            </div>
                            <div>
                                <p style="font-size: 12px; color: #64748b;">MAE</p>
                                <p style="font-size: 18px; font-weight: 600; color: #64748b;">${metrics.test_mae.toFixed(2)}</p>
                            </div>
                            <div>
                                <p style="font-size: 12px; color: #64748b;">Muestras</p>
                                <p style="font-size: 18px; font-weight: 600; color: #64748b;">${metrics.samples}</p>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            metricsHTML += '</div>';
        }
        
        resultsContainer.innerHTML = `
            <div style="margin-top: 20px; padding: 30px; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 48px;">✅</div>
                    <h3 style="color: #10b981; margin-top: 15px;">Entrenamiento Completado</h3>
                    <p style="color: #64748b; margin-top: 10px;">
                        Los modelos han sido entrenados exitosamente
                    </p>
                </div>
                ${metricsHTML}
                <div style="margin-top: 20px; padding: 15px; background: #f0fdf4; border-radius: 8px;">
                    <p style="color: #166534; font-weight: 600; margin-bottom: 5px;">✓ Modelos guardados</p>
                    <p style="color: #15803d; font-size: 14px;">
                        Ahora puede generar predicciones desde la pestaña "Predicciones ML"
                    </p>
                </div>
            </div>
        `;

    } catch (error) {
        console.error('Error entrenando modelos:', error);
        resultsContainer.innerHTML = `
            <div style="margin-top: 20px; padding: 30px; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;">
                <div style="font-size: 48px;">❌</div>
                <h3 style="color: #ef4444; margin-top: 15px;">Error en el entrenamiento</h3>
                <p style="color: #64748b; margin-top: 10px;">${error.message}</p>
                <div style="margin-top: 20px; padding: 15px; background: #fef2f2; border-radius: 8px; text-align: left;">
                    <p style="color: #991b1b; font-weight: 600; margin-bottom: 10px;">Posibles causas:</p>
                    <ul style="color: #7f1d1d; margin-left: 20px;">
                        <li>No hay suficientes datos en MongoDB (mínimo 50 registros)</li>
                        <li>Permisos insuficientes (solo administradores)</li>
                        <li>Error de conexión con la API</li>
                    </ul>
                    <p style="color: #991b1b; margin-top: 15px; font-weight: 600;">Solución:</p>
                    <ol style="color: #7f1d1d; margin-left: 20px;">
                        <li>Verificar que está logueado como administrador</li>
                        <li>Cargar datos: <code>python -m src.data_ingestion.csv_producer</code></li>
                        <li>Verificar logs de la API en la terminal</li>
                    </ol>
                </div>
                <button onclick="trainModels()" class="btn btn-warning" style="margin-top: 20px;">
                    🔄 Reintentar
                </button>
            </div>
        `;
    }
}

/**
 * Cargar logs del sistema
 */
async function loadLogs() {
    const logsContainer = document.getElementById('systemLogs');
    if (!logsContainer) return;

    logsContainer.innerHTML = '<p style="color: #64748b;">Cargando logs...</p>';

    try {
        // TODO: Implementar endpoint de logs
        logsContainer.innerHTML = `
            <div style="margin-top: 20px; padding: 20px; background: white; border-radius: 8px;">
                <p style="color: #64748b;">Funcionalidad de logs en desarrollo</p>
            </div>
        `;
    } catch (error) {
        console.error('Error cargando logs:', error);
        logsContainer.innerHTML = `
            <p style="color: #ef4444;">Error cargando logs: ${error.message}</p>
        `;
    }
}