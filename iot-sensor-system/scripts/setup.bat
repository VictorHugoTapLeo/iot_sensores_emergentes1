@echo off
REM Script de setup para Windows
REM Sistema IoT GAMC

echo ============================================================
echo   SISTEMA IoT GAMC - SETUP PARA WINDOWS
echo ============================================================
echo.

REM Verificar Docker
echo Verificando Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker no esta instalado
    echo Instale Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker encontrado

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose no esta instalado
    pause
    exit /b 1
)
echo [OK] Docker Compose encontrado

REM Verificar Python
echo.
echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado
    echo Instale Python 3.9+ desde: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python encontrado

REM Crear directorios
echo.
echo Creando directorios...
if not exist "data" mkdir data
if not exist "src\ml\models" mkdir src\ml\models
if not exist "logs" mkdir logs
echo [OK] Directorios creados

REM Crear .env si no existe
if not exist ".env" (
    echo.
    echo Creando archivo .env...
    (
        echo # Kafka Configuration
        echo KAFKA_BOOTSTRAP_SERVERS=localhost:9092
        echo KAFKA_TOPIC_AIRE=sensor-aire
        echo KAFKA_TOPIC_SONIDO=sensor-sonido
        echo KAFKA_TOPIC_SOTERRADO=sensor-soterrado
        echo.
        echo # MongoDB Configuration
        echo MONGODB_URI=mongodb://admin:admin123@localhost:27017/
        echo MONGODB_DATABASE=iot_sensors
        echo.
        echo # PostgreSQL Configuration
        echo POSTGRES_HOST=localhost
        echo POSTGRES_PORT=5432
        echo POSTGRES_DB=iot_system
        echo POSTGRES_USER=admin
        echo POSTGRES_PASSWORD=admin123
        echo.
        echo # JWT Configuration
        echo JWT_SECRET_KEY=cambiar-en-produccion
        echo JWT_EXPIRATION_HOURS=24
        echo.
        echo # API Configuration
        echo API_HOST=0.0.0.0
        echo API_PORT=5000
        echo API_DEBUG=True
    ) > .env
    echo [OK] Archivo .env creado
) else (
    echo [OK] Archivo .env ya existe
)

REM Crear entorno virtual
echo.
echo Configurando entorno virtual Python...
if not exist "venv" (
    python -m venv venv
    echo [OK] Entorno virtual creado
) else (
    echo [OK] Entorno virtual ya existe
)

REM Activar entorno virtual e instalar dependencias
echo.
echo Instalando dependencias Python...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo [OK] Dependencias instaladas

REM Iniciar Docker Compose
echo.
echo Iniciando servicios Docker...
docker-compose up -d

REM Esperar servicios
echo.
echo Esperando a que los servicios esten listos (30 segundos)...
timeout /t 30 /nobreak >nul

REM Verificar servicios
echo.
echo Estado de servicios:
docker-compose ps

REM Inicializar bases de datos
echo.
echo Inicializando bases de datos...
python scripts\init_db.py

REM Crear guía rápida
echo.
echo Creando guia de inicio rapido...
(
    echo # Guia de Inicio Rapido - Windows
    echo.
    echo ## Servicios Iniciados
    echo.
    echo - Kafka: localhost:9092
    echo - MongoDB: localhost:27017
    echo - PostgreSQL: localhost:5432
    echo.
    echo ## Proximos Pasos
    echo.
    echo 1. Activar entorno virtual:
    echo    venv\Scripts\activate.bat
    echo.
    echo 2. Generar datos:
    echo    python simulador_sensores.py
    echo.
    echo 3. Enviar a Kafka:
    echo    python -m src.data_ingestion.csv_producer
    echo.
    echo 4. Consumir datos (nueva terminal^):
    echo    python -m src.data_ingestion.kafka_consumer
    echo.
    echo 5. Entrenar ML:
    echo    python -m src.ml.trainer
    echo.
    echo 6. Iniciar API:
    echo    python -m src.api.app
    echo.
    echo 7. Abrir navegador:
    echo    start frontend\index.html
    echo.
    echo ## Comandos Utiles
    echo.
    echo Ver logs: docker-compose logs -f
    echo Detener: docker-compose down
    echo Reiniciar: docker-compose restart
) > QUICKSTART_WINDOWS.md

echo [OK] Guia creada: QUICKSTART_WINDOWS.md

REM Resumen
echo.
echo ============================================================
echo   SETUP COMPLETADO
echo ============================================================
echo.
echo [OK] Sistema configurado correctamente
echo.
echo PROXIMOS PASOS:
echo.
echo 1. Activar entorno virtual:
echo    venv\Scripts\activate.bat
echo.
echo 2. Generar datos:
echo    python simulador_sensores.py
echo.
echo 3. Ver guia completa:
echo    type QUICKSTART_WINDOWS.md
echo.
echo Para detener servicios: docker-compose down
echo.
pause