📋 Requisitos Previos
Software Necesario

Docker Desktop (Recomendado)

Windows/Mac: https://www.docker.com/products/docker-desktop
Linux: https://docs.docker.com/engine/install/


Python 3.9+

Windows/Mac: https://www.python.org/downloads/
Linux: sudo apt install python3 python3-pip python3-venv


Git (opcional)

https://git-scm.com/downloads

🚀 PASO 1: Preparar el Proyecto
1.1 Descargar o Clonar
# Opción A: Si tienes git
git clone <url-del-repositorio>
cd iot-sensor-system

# Opción B: Descargar ZIP y extraer
# Luego navegar a la carpeta
cd iot-sensor-system

1.2 Verificar Estructura
Asegúrate de tener esta estructura:

iot-sensor-system/
├── docker-compose.yml
├── requirements.txt
├── .env (o .env.example)
├── simulador_sensores.py
├── src/
├── frontend/
└── scripts/

🔧 PASO 2: Ejecutar Setup Automático
scripts\setup.bat
¿Qué hace el setup?

✅ Verifica Docker y Python
✅ Crea directorios necesarios
✅ Crea archivo .env
✅ Crea entorno virtual Python
✅ Instala dependencias
✅ Inicia servicios Docker (Kafka, MongoDB, PostgreSQL)
✅ Inicializa bases de datos

📊 PASO 3: Generar Datos de Prueba
3.1 Activar Entorno Virtual
venv\Scripts\activate.bat

3.2 Ejecutar Simulador
python simulador_sensores.py

3.3 Configurar Simulación
Cuando el menú aparezca:
Opciones:
1. Sensor de Calidad de Aire
2. Sensor de Sonido
3. Sensor Soterrado
4. Simular TODOS los sensores  ← SELECCIONAR ESTA

¿Cuántas lecturas desea simular por sensor? 200  ← INGRESAR NÚMERO

¿Cómo desea generar los datos?
1. Con intervalo en SEGUNDOS
2. Con intervalo en MINUTOS  ← SELECCIONAR ESTA
3. MODO RÁFAGA

¿Cada cuántos minutos? 5  ← INGRESAR NÚMERO

Fecha y hora de inicio: 2024-12-01 00:00  ← FECHA PASADA

Resultado: Se crearán 3 archivos CSV en la carpeta data/:

simulacion_aire_XXXXXXXXX.csv
simulacion_sonido_XXXXXXXXX.csv
simulacion_soterrado_XXXXXXXXX.csv

🔄 PASO 4: Enviar Datos a Kafka

4.1 Ejecutar Productor
python -m src.data_ingestion.csv_producer

4.2 Confirmar Envío
El script mostrará:
✓ Archivos CSV encontrados: 3
  - simulacion_aire_20241209_143052.csv
  - simulacion_sonido_20241209_143052.csv
  - simulacion_soterrado_20241209_143052.csv

¿Desea continuar? (s/n): s  ← ESCRIBIR 's'
Resultado: Los datos se enviarán a Kafka topic por topic.

💾 PASO 5: Consumir y Guardar en MongoDB
5.1 Abrir Nueva Terminal
Importante: No cerrar la terminal anterior. Abrir una NUEVA terminal.

5.2 Activar Entorno Virtual
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate.bat

5.3 Ejecutar Consumidor
python -m src.data_ingestion.kafka_consumer

Resultado: Verás mensajes como:
✓ Conectado a MongoDB: iot_sensors
✓ Consumidor Kafka conectado
🚀 Iniciando consumo de mensajes...
✓ Procesados: 10 mensajes
✓ Procesados: 20 mensajes
...
⚠️ MANTENER ESTE PROCESO EJECUTÁNDOSE

🤖 PASO 6: Entrenar Modelos de Machine Learning
6.1 Abrir Nueva Terminal (3ra)

6.2 Activar Entorno Virtual
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate.bat

6.3 Ejecutar Entrenamiento
python -m src.ml.trainer

6.4 Configurar Entrenamiento
Sensores disponibles:
  1. aire
  2. sonido
  3. soterrado
  4. Entrenar TODOS  ← SELECCIONAR 4

¿Cuántos días de datos usar? 60  ← DEJAR POR DEFECTO O CAMBIAR

Resultado: Modelos entrenados se guardarán en src/ml/models/

🌐 PASO 7: Iniciar API Backend
7.1 Abrir Nueva Terminal (4ta)

7.2 Activar Entorno Virtual
venv\Scripts\activate.bat

7.3 Iniciar API
python -m src.api.app

Resultado: Verás:
Iniciando servidor en 0.0.0.0:5000
 * Running on http://0.0.0.0:5000

⚠️ MANTENER ESTE PROCESO EJECUTÁNDOSE

🖥️ PASO 8: Abrir Frontend
Opción A: Abrir Archivo Directamente (Más Fácil)
start frontend\index.html

Opción B: Servir con HTTP Server
# En una nueva terminal, desde la carpeta frontend/
cd frontend
python -m http.server 8080

# Luego abrir en navegador:
http://localhost:8080

🔐 PASO 9: Login y Explorar
9.1 Login
Usar cualquiera de estos usuarios:
Usuario Contraseña Rol 
admin admin123 Administrador (Recomendado)
alcalde alcalde123 Ejecutivo (Alcalde)
director director123 Ejecutivo (Director)
usuario usuario123 (Usuario) 

9.2 Explorar Dashboard
Tab Resumen: Ver estadísticas generales
Tab Calidad de Aire: Gráficos de CO2, Temperatura, Humedad, Presión
Tab Nivel de Sonido: Gráficos de decibeles
Tab Nivel de Líquido: Gráfico de distancia
Tab Predicciones ML:

Seleccionar sensor
Seleccionar período (7 o 30 días)
Clic en "Generar Predicciones"


Tab Administración (solo admin):

Entrenar nuevos modelos
Ver logs del sistema

🎓 PASO 10: Generar Predicciones
10.1 Ir a Tab "Predicciones ML"
10.2 Configurar Predicción

Seleccionar Sensor: Calidad de Aire / Sonido / Líquido
Seleccionar Período: 7 días / 30 días
Clic: "🔮 Generar Predicciones"

10.3 Ver Resultados
El sistema mostrará:

✅ Gráficos comparativos (Histórico vs Predicción)
📊 Estadísticas de predicciones (Promedio, Min, Max, Desv. Est.)
📈 Valores predichos para cada variable

📈 Resumen de Procesos Activos
Al final deberías tener estos procesos ejecutándose:
Terminal 1: Kafka Consumer (MongoDB)
Terminal 2: Flask API (Backend)
Terminal 3: (Libre - para comandos)
Navegador: Frontend Dashboard
Docker: Kafka, MongoDB, PostgreSQL, Redis

🔍 Verificar que Todo Funciona
Verificar Servicios Docker
docker-compose ps

# Deberías ver todos los servicios "Up"

Verificar Datos en MongoDB
python -c "from src.database.mongodb_manager import MongoDBManager; \
    db = MongoDBManager(); \
    print('Aire:', db.count_documents('aire')); \
    print('Sonido:', db.count_documents('sonido')); \
    print('Soterrado:', db.count_documents('soterrado'))"

Verificar API
curl http://localhost:5000/health

# Debería retornar: {"status":"healthy"}

🛠️ Comandos Útiles
Ver Logs de Servicios
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f kafka
docker-compose logs -f mongodb
docker-compose logs -f postgres

Reiniciar Servicios
# Reiniciar todo
docker-compose restart

# Reiniciar servicio específico
docker-compose restart kafka

Detener Todo
# Detener sin eliminar datos
docker-compose stop

# Detener y eliminar contenedores (mantiene datos)
docker-compose down

# Detener y eliminar TODO (incluye datos)
docker-compose down -v

Limpiar y Empezar de Nuevo
# 1. Detener todo y eliminar datos
docker-compose down -v

# 2. Eliminar modelos ML
rm -rf src/ml/models/*

# 3. Eliminar CSVs
rm -rf data/*.csv

# 4. Volver a ejecutar setup
./scripts/setup.sh  # o setup.bat en Windows

❓ Solución de Problemas Comunes
Problema: Kafka no conecta
Solución:

docker-compose restart kafka zookeeper
# Esperar 30 segundos

Problema: MongoDB no conecta
Solución:

docker-compose restart mongodb
# Esperar 10 segundos

Problema: No se generan predicciones
Causas posibles:

No hay datos suficientes (mínimo 50 registros)
Modelos no entrenados
Datos muy antiguos

Solución:

# 1. Verificar datos
python -c "from src.database.mongodb_manager import MongoDBManager; \
    db = MongoDBManager(); \
    print(db.count_documents('aire'))"

# 2. Re-entrenar modelos
python -m src.ml.trainer

# 3. Generar nuevos datos
python simulador_sensores.py

Problema: Frontend no carga datos
Solución:

Verificar que la API está ejecutándose
Abrir Consola del Navegador (F12)
Revisar errores de red
Verificar que el token JWT es válido (hacer logout/login)

Problema: Error "Token inválido"
Solución:

// En el navegador, consola (F12):
localStorage.clear();
// Luego recargar página y hacer login de nuevo

📊 Métricas de Calidad ML
¿Cómo saber si los modelos son buenos?
El sistema muestra métricas automáticamente:

R² (R cuadrado):

≥ 0.85: Excelente ✅
0.70 - 0.84: Bueno 👍
< 0.70: Necesita más datos o ajuste ⚠️


RMSE (Error Cuadrático Medio):

Más bajo = mejor
Comparar con rango de valores


MAE (Error Absoluto Medio):

Más bajo = mejor
Indica error promedio en unidades originales

