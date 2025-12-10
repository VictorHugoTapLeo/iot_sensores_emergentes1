#!/bin/bash

# Script de setup completo del Sistema IoT GAMC
# Autor: Sistema IoT GAMC
# Fecha: 2025

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de utilidad
print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Verificar que se está ejecutando en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto"
    exit 1
fi

print_header "SISTEMA IoT GAMC - SETUP AUTOMATIZADO"

# 1. Verificar Docker
print_info "Verificando Docker..."
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    print_success "Docker y Docker Compose encontrados"
    docker --version
    docker-compose --version
else
    print_error "Docker o Docker Compose no están instalados"
    print_info "Instale Docker Desktop desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 2. Verificar Python
print_info "Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python encontrado: $PYTHON_VERSION"
else
    print_error "Python 3 no está instalado"
    exit 1
fi

# 3. Crear directorios necesarios
print_info "Creando estructura de directorios..."
mkdir -p data
mkdir -p src/ml/models
mkdir -p logs
print_success "Directorios creados"

# 4. Verificar archivo .env
print_info "Verificando configuración..."
if [ ! -f ".env" ]; then
    print_warning "Archivo .env no encontrado"
    
    if [ -f ".env.example" ]; then
        print_info "Copiando .env.example a .env"
        cp .env.example .env
        print_success "Archivo .env creado"
        print_warning "⚠ IMPORTANTE: Revise y modifique .env según sea necesario"
    else
        print_error "Archivo .env.example no encontrado"
        print_info "Creando .env con configuración por defecto..."
        
        cat > .env << 'EOF'
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_AIRE=sensor-aire
KAFKA_TOPIC_SONIDO=sensor-sonido
KAFKA_TOPIC_SOTERRADO=sensor-soterrado
KAFKA_CONSUMER_GROUP=iot-consumers

# MongoDB Configuration
MONGODB_URI=mongodb://admin:admin123@localhost:27017/
MONGODB_DATABASE=iot_sensors
MONGODB_COLLECTION_AIRE=datos_aire
MONGODB_COLLECTION_SONIDO=datos_sonido
MONGODB_COLLECTION_SOTERRADO=datos_soterrado

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=iot_system
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT Configuration
JWT_SECRET_KEY=cambiar-en-produccion-$(openssl rand -hex 32)
JWT_EXPIRATION_HOURS=24

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=True

# ML Configuration
ML_PREDICTION_DAYS_SHORT=7
ML_PREDICTION_DAYS_LONG=30

# Data Ingestion
CSV_DATA_PATH=data
CSV_BATCH_SIZE=100
KAFKA_SEND_INTERVAL=0.1

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
        print_success "Archivo .env creado con configuración por defecto"
    fi
else
    print_success "Archivo .env encontrado"
fi

# 5. Crear entorno virtual Python
print_info "Configurando entorno virtual Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Entorno virtual creado"
else
    print_success "Entorno virtual ya existe"
fi

# Activar entorno virtual
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || {
    print_warning "No se pudo activar el entorno virtual automáticamente"
    print_info "Active manualmente con: source venv/bin/activate"
}

# 6. Instalar dependencias Python
print_info "Instalando dependencias Python..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
print_success "Dependencias instaladas"

# 7. Iniciar servicios Docker
print_info "Iniciando servicios Docker..."
docker-compose up -d

# Esperar a que los servicios estén listos
print_info "Esperando a que los servicios estén listos (30 segundos)..."
sleep 30

# Verificar servicios
print_info "Verificando estado de servicios..."
docker-compose ps

# 8. Inicializar bases de datos
print_info "Inicializando bases de datos..."
python3 scripts/init_db.py

# 9. Crear archivo README con instrucciones
print_info "Creando guía de inicio rápido..."
cat > QUICKSTART.md << 'EOF'
# 🚀 Guía de Inicio Rápido

## Servicios Iniciados

Los siguientes servicios están ejecutándose:

- **Kafka**: localhost:9092
- **MongoDB**: localhost:27017 (usuario: admin, contraseña: admin123)
- **PostgreSQL**: localhost:5432 (usuario: admin, contraseña: admin123)
- **Redis**: localhost:6379

## Próximos Pasos

### 1. Generar Datos de Prueba

```bash
python simulador_sensores.py
```

Siga las instrucciones del simulador para generar archivos CSV.

### 2. Enviar Datos a Kafka

```bash
python -m src.data_ingestion.csv_producer
```

### 3. Consumir Datos (en otra terminal)

```bash
python -m src.data_ingestion.kafka_consumer
```

Mantenga este proceso ejecutándose.

### 4. Entrenar Modelos ML

```bash
python -m src.ml.trainer
```

### 5. Iniciar API Backend

```bash
python -m src.api.app
```

La API estará disponible en: http://localhost:5000

### 6. Abrir Frontend

Abra en su navegador: `frontend/index.html`

O sirva con:
```bash
cd frontend
python -m http.server 8080
```

Luego abra: http://localhost:8080

## Usuarios por Defecto

| Usuario  | Contraseña  | Rol           |
|----------|-------------|---------------|
| alcalde  | alcalde123  | Alcalde       |
| director | director123 | Director      |
| admin    | admin123    | Administrador |
| usuario  | usuario123  | Usuario       |

## Comandos Útiles

### Ver logs de servicios
```bash
docker-compose logs -f [servicio]
```

### Detener servicios
```bash
docker-compose down
```

### Reiniciar servicios
```bash
docker-compose restart
```

### Ver estado de servicios
```bash
docker-compose ps
```

## Solución de Problemas

### Kafka no conecta
```bash
docker-compose restart kafka zookeeper
```

### MongoDB no conecta
```bash
docker-compose restart mongodb
```

### Limpiar todo y empezar de nuevo
```bash
docker-compose down -v
docker-compose up -d
python scripts/init_db.py
```
EOF

print_success "Guía creada: QUICKSTART.md"

# Resumen final
print_header "SETUP COMPLETADO"

print_success "Sistema configurado correctamente"
echo ""
print_info "Servicios Docker iniciados:"
docker-compose ps
echo ""

print_header "PRÓXIMOS PASOS"
echo ""
echo "1. Generar datos de prueba:"
echo "   ${GREEN}python simulador_sensores.py${NC}"
echo ""
echo "2. Ver la guía rápida:"
echo "   ${GREEN}cat QUICKSTART.md${NC}"
echo ""
echo "3. Enviar datos a Kafka:"
echo "   ${GREEN}python -m src.data_ingestion.csv_producer${NC}"
echo ""
echo "4. Consumir datos (en otra terminal):"
echo "   ${GREEN}python -m src.data_ingestion.kafka_consumer${NC}"
echo ""
echo "5. Entrenar modelos ML:"
echo "   ${GREEN}python -m src.ml.trainer${NC}"
echo ""
echo "6. Iniciar API:"
echo "   ${GREEN}python -m src.api.app${NC}"
echo ""
echo "7. Abrir frontend:"
echo "   ${GREEN}open frontend/index.html${NC}"
echo ""

print_info "Para detener los servicios: ${GREEN}docker-compose down${NC}"
print_info "Para ver logs: ${GREEN}docker-compose logs -f${NC}"
echo ""

print_success "¡Listo para empezar! 🚀"