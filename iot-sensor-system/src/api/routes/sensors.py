"""
Sensors Routes - Rutas para datos de sensores
"""
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.database.mongodb_manager import MongoDBManager
from src.database.postgres_manager import PostgresManager
from src.api.middleware.auth_middleware import token_required
from src.config.settings import Config

logger = logging.getLogger(__name__)

bp = Blueprint('sensors', __name__)
mongo_db = MongoDBManager()
postgres_db = PostgresManager()

@bp.route('/types', methods=['GET'])
@token_required
def get_sensor_types():
    """Obtener tipos de sensores disponibles"""
    return jsonify({
        'sensor_types': Config.SENSOR_TYPES,
        'descriptions': {
            'aire': 'Calidad de Aire (CO2, Temperatura, Humedad, Presión)',
            'sonido': 'Nivel de Sonido (Decibeles)',
            'soterrado': 'Nivel de Líquido (Distancia)'
        }
    }), 200

@bp.route('/<sensor_type>/latest', methods=['GET'])
@token_required
def get_latest_data(sensor_type):
    """Obtener últimos datos de un sensor"""
    try:
        if sensor_type not in Config.SENSOR_TYPES:
            return jsonify({'error': 'Tipo de sensor inválido'}), 400
        
        limit = request.args.get('limit', 100, type=int)
        data = mongo_db.get_latest_data(sensor_type, limit)
        
        postgres_db.log_action(
            request.user['user_id'],
            'READ',
            f'sensors/{sensor_type}/latest',
            f'limit={limit}'
        )
        
        clean_data = []
        for item in data:
            item['_id'] = str(item['_id'])
            if 'processed_at' in item:
                item['processed_at'] = item['processed_at'].isoformat()
            clean_data.append(item)
        
        return jsonify({
            'sensor_type': sensor_type,
            'count': len(clean_data),
            'data': clean_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo últimos datos: {e}")
        return jsonify({'error': 'Error en el servidor'}), 500

@bp.route('/<sensor_type>/statistics', methods=['GET'])
@token_required
def get_statistics(sensor_type):
    """Obtener estadísticas de un sensor"""
    try:
        if sensor_type not in Config.SENSOR_TYPES:
            return jsonify({'error': 'Tipo de sensor inválido'}), 400
        
        hours = request.args.get('hours', 24, type=int)
        stats = mongo_db.get_statistics(sensor_type, hours)
        
        return jsonify({
            'sensor_type': sensor_type,
            'hours': hours,
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'error': 'Error en el servidor'}), 500

@bp.route('/summary', methods=['GET'])
@token_required
def get_summary():
    """Obtener resumen de todos los sensores"""
    try:
        summary = {}
        
        for sensor_type in Config.SENSOR_TYPES:
            count = mongo_db.count_documents(sensor_type)
            latest = mongo_db.get_latest_data(sensor_type, 1)
            
            summary[sensor_type] = {
                'total_records': count,
                'latest_update': latest[0]['time'] if latest else None
            }
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen: {e}")
        return jsonify({'error': 'Error en el servidor'}), 500