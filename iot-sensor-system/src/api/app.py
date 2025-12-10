"""
Flask API - Backend principal del sistema IoT
"""
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from src.config.settings import Config
from src.api.routes import auth
from src.api.routes import sensors
from src.api.routes import predictions
from src.api.middleware.auth_middleware import token_required

# Configurar logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.JWT_SECRET_KEY

# Habilitar CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Socket.IO para comunicación en tiempo real
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Registrar Blueprints
app.register_blueprint(auth.bp, url_prefix='/api/auth')
app.register_blueprint(sensors.bp, url_prefix='/api/sensors')
app.register_blueprint(predictions.bp, url_prefix='/api/predictions')

# Ruta principal
@app.route('/')
def index():
    """Página principal"""
    return jsonify({
        'service': 'Sistema IoT GAMC',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth',
            'sensors': '/api/sensors',
            'predictions': '/api/predictions'
        }
    })

# Ruta de health check
@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy'}), 200

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    """Error 404"""
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Error 500"""
    logger.error(f"Error interno: {error}")
    return jsonify({'error': 'Error interno del servidor'}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    logger.info('Cliente conectado via WebSocket')

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    logger.info('Cliente desconectado')

@socketio.on('subscribe')
def handle_subscribe(data):
    """Suscribirse a actualizaciones de sensor"""
    sensor_type = data.get('sensor_type')
    logger.info(f'Cliente suscrito a: {sensor_type}')

def run_app():
    """Ejecutar aplicación"""
    logger.info(f"Iniciando servidor en {Config.API_HOST}:{Config.API_PORT}")
    socketio.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=Config.API_DEBUG
    )

if __name__ == '__main__':
    run_app()