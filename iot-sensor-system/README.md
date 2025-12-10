# 🌐 Sistema IoT GAMC - Monitoreo de Sensores en Tiempo Real

Sistema completo de captura, análisis, visualización y predicción con Machine Learning para sensores IoT del Gobierno Autónomo Municipal de Cochabamba.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [API](#api)
- [Machine Learning](#machine-learning)
- [Troubleshooting](#troubleshooting)

## ✨ Características

### Funcionalidades Principales

- ✅ **Ingestion en Tiempo Real**: Kafka para procesamiento asíncrono de datos
- ✅ **Almacenamiento Dual**: MongoDB (NoSQL) + PostgreSQL (SQL)
- ✅ **Visualización Interactiva**: Dashboard en tiempo real con gráficos dinámicos
- ✅ **Machine Learning**: Predicciones a 7 y 30 días usando Random Forest
- ✅ **Autenticación JWT**: Sistema seguro de usuarios y roles
- ✅ **Multi-Sensor**: Soporta sensores de aire, sonido y nivel de líquido
- ✅ **Dockerizado**: Deploy completo con Docker Compose

### Tipos de Sensores

1. **Sensores de Calidad de Aire** 🌬️
   - CO2 (ppm)
   - Temperatura (°C)
   - Humedad (%)
   - Presión Barométrica (hPa)

2. **Sensores de Sonido** 🔊
   - LAeq (dB)
   - LAI (dB)
   - LAImax (dB)

3. **Sensores Soterrados** 💧
   - Nivel de líquido (Distancia en cm)

## 🏗️ Arquitectura

```
┌─────────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│   CSV Data  │───▶│  Kafka  │───▶│ MongoDB  │───▶│ Frontend │
└─────────────┘    └─────────┘    └──────────┘    └──────────┘
                                         │              │
                                         │              │
                                    ┌────▼────┐    ┌───▼────┐
                                    │   ML    │    │  Auth  │
                                    │ Models  │    │ (JWT)  │
                                    └─────────┘    └────────┘
                                                        │
                                                   ┌────▼────┐
                                                   │PostgreSQL│
                                                   └─────────┘
```

### Capas del Sistema

1. **Capa de Fuente de Datos**: Archivos CSV generados por `simulador_sensores.py`
2. **Capa de Ingestión**: Productor Kafka (`csv_producer.py`)
3. **Capa de Procesamiento**: Consumidor Kafka → MongoDB (`kafka_consumer.py`)
4. **Capa de Almacenamiento**: 
   - MongoDB: Datos de sensores
   - PostgreSQL: Usuarios, logs, autenticación
5. **Capa de Machine Learning**: 
   - Entrenamiento: `trainer.py`
   - Predicción: `predictor.py`
6. **Capa de API**: Flask REST API con WebSockets
7. **Capa de Visualización**: Frontend HTML/JS con Chart.js

## 📦 Requisitos

### Software Necesario

- Docker & Docker Compose (recomendado) **O**
- Python 3.9+
- Node.js (opcional, para desarrollo)

### Hardware Recomendado

- CPU: 4 cores
- RAM: 8 GB mínimo
- Disco: 10 GB libres

## 🚀 Instalación

### Opción 1: Con Docker (Recomendado)

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd iot-sensor-system

# 2. Levantar servicios
docker-compose up -d

# 3. Verificar servicios
docker-compose ps

# Los servicios estarán disponibles en:
# - Kafka: localhost:9092
# - MongoDB: localhost:27017
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### Opción 2: Instalación Local

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 4. Instalar y configurar Kafka, MongoDB, PostgreSQL manualmente
```

## ⚙️ Configuración

### 1. Variables de Entorno

Editar el archivo `.env`:

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# MongoDB
MONGODB_URI=mongodb://admin:admin123@localhost:27017/
MONGODB_DATABASE=iot_sensors

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_DB=iot_system
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123

# JWT
JWT_SECRET_KEY=cambiar-en-produccion

# API
API_PORT=5000
```

### 2. Inicializar Bases de Datos

```bash
# Inicializar PostgreSQL (crea usuarios por defecto)
python scripts/init_db.py
```

## 📊 Uso

### Paso 1: Generar Datos de Simulación

```bash
# Generar datos CSV con el simulador
python simulador_sensores.py

# Seguir instrucciones del menú interactivo
# Los archivos se generarán en la carpeta data/
```

### Paso 2: Enviar Datos a Kafka

```bash
# Enviar datos CSV a Kafka
python -m src.data_ingestion.csv_producer

# El script buscará automáticamente archivos en data/
# y los enviará a los topics correspondientes
```

### Paso 3: Consumir y Guardar en MongoDB

```bash
# En una terminal separada, iniciar consumidor
python -m src.data_ingestion.kafka_consumer

# El consumidor guardará automáticamente los datos en MongoDB
# Mantener este proceso ejecutándose
```

### Paso 4: Entrenar Modelos ML

```bash
# Entrenar modelos de Machine Learning
python -m src.ml.trainer

# Seleccionar sensor y días de entrenamiento
# Los modelos se guardarán en src/ml/models/
```

### Paso 5: Iniciar API

```bash
# Iniciar servidor Flask
python -m src.api.app

# API disponible en: http://localhost:5000
```

### Paso 6: Abrir Frontend

```bash
# Abrir en navegador
open frontend/index.html

# O servir con un servidor HTTP
cd frontend
python -m http.server 8080
# Luego abrir: http://localhost:8080
```

### Usuarios por Defecto

| Usuario   | Contraseña   | Rol                |
|-----------|--------------|-------------------|
| alcalde   | alcalde123   | Ejecutivo (Alcalde) |
| director  | director123  | Ejecutivo (Director)|
| admin     | admin123     | Administrador      |
| usuario   | usuario123   | Usuario Operativo  |

## 📁 Estructura del Proyecto

```
iot-sensor-system/
├── data/                      # Datos CSV
├── src/
│   ├── config/               # Configuración
│   ├── data_ingestion/       # Kafka producer/consumer
│   ├── database/             # Gestores de BD
│   ├── ml/                   # Machine Learning
│   │   ├── models/           # Modelos entrenados
│   │   ├── trainer.py
│   │   └── predictor.py
│   ├── api/                  # Flask API
│   │   ├── routes/
│   │   └── middleware/
│   └── utils/                # Utilidades
├── frontend/                 # Dashboard web
│   ├── index.html
│   ├── css/
│   └── js/
├── docker-compose.yml
├── requirements.txt
└── .env
```

## 🔌 API

### Endpoints Principales

#### Autenticación

```
POST /api/auth/login
POST /api/auth/verify
GET  /api/auth/profile
```

#### Sensores

```
GET  /api/sensors/types
GET  /api/sensors/{type}/latest?limit=100
GET  /api/sensors/{type}/range?start_date=...&end_date=...
GET  /api/sensors/{type}/statistics?hours=24
GET  /api/sensors/summary
```

#### Predicciones

```
POST /api/predictions/{type}/predict
POST /api/predictions/{type}/predict/multiple
GET  /api/predictions/{type}/latest
POST /api/predictions/{type}/train  (solo admin)
POST /api/predictions/train/all      (solo admin)
```

### Ejemplo de Uso

```javascript
// Login
const response = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
    })
});

const { token } = await response.json();

// Obtener datos de sensores
const sensorsResponse = await fetch('http://localhost:5000/api/sensors/aire/latest?limit=50', {
    headers: { 'Authorization': `Bearer ${token}` }
});

const data = await sensorsResponse.json();
```

## 🤖 Machine Learning

### Características del Modelo

- **Algoritmo**: Random Forest Regressor
- **Features**: 
  - Características temporales (hora, día, mes)
  - Features cíclicos (sin/cos)
  - Índice temporal normalizado
- **Métricas**: R², RMSE, MAE

### Entrenar Modelos

```bash
python -m src.ml.trainer

# Opciones:
# 1. Entrenar sensor específico
# 2. Entrenar todos los sensores
# 3. Configurar días de entrenamiento (30-365)
```

### Generar Predicciones

```bash
python -m src.ml.predictor

# Genera predicciones para:
# - 7 días (hourly)
# - 30 días (daily)
```

### Métricas de Evaluación

El sistema calcula automáticamente:
- **R² Score**: Calidad del ajuste
- **RMSE**: Error cuadrático medio
- **MAE**: Error absoluto medio
- **Precisión**: ≥ 70% para aceptable, ≥ 85% para excelente

## 🛠️ Troubleshooting

### Kafka no conecta

```bash
# Verificar que Kafka esté ejecutándose
docker-compose ps kafka

# Reiniciar Kafka
docker-compose restart kafka zookeeper
```

### MongoDB no conecta

```bash
# Verificar MongoDB
docker-compose ps mongodb

# Ver logs
docker-compose logs mongodb
```

### Error en modelos ML

```bash
# Verificar que hay datos suficientes
python -c "from src.database.mongodb_manager import MongoDBManager; \
    db = MongoDBManager(); \
    print(db.count_documents('aire'))"

# Re-entrenar modelos
python -m src.ml.trainer
```

### Frontend no carga datos

1. Verificar que la API está ejecutándose
2. Verificar CORS en el navegador (F12 → Console)
3. Verificar que el token JWT es válido

## 📝 Licencia

Este proyecto es propiedad del GAMC y está destinado exclusivamente para fines académicos.

## 👥 Autor

- Estudiante de Tecnologías Emergentes I Victor Hugo Tapia Leon
- Universidad del Valle
- Octubre 2025

