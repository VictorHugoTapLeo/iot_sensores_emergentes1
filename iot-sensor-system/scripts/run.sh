#!/bin/bash

# Script para ejecutar el sistema completo
# Autor: Sistema IoT GAMC

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    print_error "Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

print_header "EJECUTANDO SISTEMA IoT GAMC"

# Activar entorno virtual
print_info "Activando entorno virtual..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || {
    print_error "No se pudo activar el entorno virtual"
    print_info "Ejecute: source venv/bin/activate"
    exit 1
}
print_success "Entorno virtual activado"

# Verificar servicios Docker
print_info "Verificando servicios Docker..."
if ! docker-compose ps | grep -q "Up"; then
    print_info "Iniciando servicios Docker..."
    docker-compose up -d
    sleep 15
fi
print_success "Servicios Docker activos"

# Menú de opciones
print_header "OPCIONES DE EJECUCIÓN"
echo "1. Generar datos de prueba"
echo "2. Enviar datos a Kafka"
echo "3. Iniciar consumidor Kafka"
echo "4. Entrenar modelos ML"
echo "5. Iniciar API Backend"
echo "6. Abrir Frontend"
echo "7. Ejecutar todo (recomendado)"
echo "8. Ver logs"
echo "9. Detener servicios"
echo "0. Salir"
echo ""

read -p "Seleccione una opción: " option

case $option in
    1)
        print_info "Generando datos de prueba..."
        python simulador_sensores.py
        ;;
    2)
        print_info "Enviando datos a Kafka..."
        python -m src.data_ingestion.csv_producer
        ;;
    3)
        print_info "Iniciando consumidor Kafka..."
        print_info "Presione Ctrl+C para detener"
        python -m src.data_ingestion.kafka_consumer
        ;;
    4)
        print_info "Entrenando modelos ML..."
        python -m src.ml.trainer
        ;;
    5)
        print_info "Iniciando API Backend..."
        print_info "API disponible en: http://localhost:5000"
        print_info "Presione Ctrl+C para detener"
        python -m src.api.app
        ;;
    6)
        print_info "Abriendo Frontend..."
        if command -v xdg-open &> /dev/null; then
            xdg-open frontend/index.html
        elif command -v open &> /dev/null; then
            open frontend/index.html
        else
            print_info "Abrir manualmente: frontend/index.html"
        fi
        ;;
    7)
        print_header "EJECUCIÓN COMPLETA"
        
        # Generar datos si no existen
        if [ ! "$(ls -A data/*.csv 2>/dev/null)" ]; then
            print_info "Generando datos de prueba..."
            python simulador_sensores.py
        fi
        
        # Enviar a Kafka en background
        print_info "Enviando datos a Kafka (background)..."
        python -m src.data_ingestion.csv_producer &
        PRODUCER_PID=$!
        
        # Esperar un poco
        sleep 5
        
        # Iniciar consumidor en background
        print_info "Iniciando consumidor (background)..."
        python -m src.data_ingestion.kafka_consumer &
        CONSUMER_PID=$!
        
        # Esperar datos
        sleep 10
        
        # Entrenar modelos si no existen
        if [ ! "$(ls -A src/ml/models/*.joblib 2>/dev/null)" ]; then
            print_info "Entrenando modelos ML..."
            python -m src.ml.trainer
        fi
        
        # Iniciar API en background
        print_info "Iniciando API (background)..."
        python -m src.api.app &
        API_PID=$!
        
        # Esperar API
        sleep 5
        
        # Abrir frontend
        print_success "Sistema completo ejecutándose!"
        print_info "API: http://localhost:5000"
        print_info "Frontend: Abriendo en navegador..."
        
        if command -v xdg-open &> /dev/null; then
            xdg-open frontend/index.html
        elif command -v open &> /dev/null; then
            open frontend/index.html
        fi
        
        print_info "Presione Ctrl+C para detener todos los procesos"
        
        # Esperar señal
        trap "kill $PRODUCER_PID $CONSUMER_PID $API_PID 2>/dev/null; exit" INT TERM
        wait
        ;;
    8)
        print_info "Mostrando logs de Docker..."
        docker-compose logs -f
        ;;
    9)
        print_info "Deteniendo servicios..."
        docker-compose down
        print_success "Servicios detenidos"
        ;;
    0)
        print_info "Saliendo..."
        exit 0
        ;;
    *)
        print_error "Opción inválida"
        exit 1
        ;;
esac