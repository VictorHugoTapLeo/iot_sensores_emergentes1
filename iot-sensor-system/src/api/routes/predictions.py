"""
Predictions Routes - Rutas para predicciones ML
"""
import logging
from flask import Blueprint, request, jsonify
from src.ml.predictor import SensorMLPredictor
from src.ml.trainer import SensorMLTrainer
from src.database.mongodb_manager import MongoDBManager
from src.database.postgres_manager import PostgresManager
from src.api.middleware.auth_middleware import token_required
from src.config.settings import Config

logger = logging.getLogger(__name__)

bp = Blueprint('predictions', __name__)
mongo_db = MongoDBManager()
postgres_db = PostgresManager()

@bp.route('/<sensor_type>/predict', methods=['POST'])
@token_required
def predict(sensor_type):
    """
    Generar predicciones para un sensor
    
    Body:
        {
            "days": 7,  # 7 o 30
            "frequency": "H"  # H (hourly) o D (daily)
        }
    """
    try:
        if sensor_type not in Config.SENSOR_TYPES:
            return jsonify({'error': 'Tipo de sensor inválido'}), 400
        
        data = request.get_json() or {}
        days = data.get('days', 7)
        frequency = data.get('frequency', 'H')
        
        if days not in [7, 30]:
            return jsonify({'error': 'days debe ser 7 o 30'}), 400
        
        if frequency not in ['H', 'D']:
            return jsonify({'error': 'frequency debe ser H o D'}), 400
        
        # Generar predicciones
        predictor = SensorMLPredictor(sensor_type)
        predictions = predictor.predict(days=days, freq=frequency)
        predictor.close()
        
        if not predictions:
            return jsonify({'error': 'No se pudieron generar predicciones'}), 500
        
        # Log de acción
        postgres_db.log_action(
            request.user['user_id'],
            'PREDICT',
            f'predictions/{sensor_type}',
            f'days={days}, freq={frequency}'
        )
        
        return jsonify(predictions), 200
        
    except Exception as e:
        logger.error(f"Error generando predicciones: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<sensor_type>/predict/multiple', methods=['POST'])
@token_required
def predict_multiple(sensor_type):
    """
    Generar predicciones para 7 y 30 días
    """
    try:
        if sensor_type not in Config.SENSOR_TYPES:
            return jsonify({'error': 'Tipo de sensor inválido'}), 400
        
        # Generar predicciones
        predictor = SensorMLPredictor(sensor_type)
        predictions = predictor.predict_multiple_periods()
        predictor.close()
        
        if not predictions:
            return jsonify({'error': 'No se pudieron generar predicciones'}), 500
        
        # Log de acción
        postgres_db.log_action(
            request.user['user_id'],
            'PREDICT_MULTIPLE',
            f'predictions/{sensor_type}',
            'Generated 7 and 30 days predictions'
        )
        
        return jsonify(predictions), 200
        
    except Exception as e:
        logger.error(f"Error generando predicciones: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<sensor_type>/latest', methods=['GET'])
@token_required
def get_latest_prediction(sensor_type):
    """
    Obtener última predicción guardada
    """
    try:
        if sensor_type not in Config.SENSOR_TYPES:
            return jsonify({'error': 'Tipo de sensor inválido'}), 400
        
        prediction = mongo_db.get_latest_prediction(sensor_type)
        
        if not prediction:
            return jsonify({'error': 'No hay predicciones disponibles'}), 404
        
        # Limpiar datos
        prediction['_id'] = str(prediction['_id'])
        if 'created_at' in prediction:
            prediction['created_at'] = prediction['created_at'].isoformat()
        
        return jsonify(prediction), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo predicción: {e}")
        return jsonify({'error': 'Error en el servidor'}), 500

@bp.route('/<sensor_type>/train', methods=['POST'])
@token_required
def train_model(sensor_type):
    """
    Entrenar modelo ML (solo admins)
    
    Body:
        {
            "days": 60  # Días de datos históricos
        }
    """
    try:
        # Solo admins pueden entrenar modelos
        if 'admin' not in request.user['role']:
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        if sensor_type not in Config.SENSOR_TYPES:
            return jsonify({'error': 'Tipo de sensor inválido'}), 400
        
        data = request.get_json() or {}
        days = data.get('days', 60)
        
        # Entrenar modelo
        trainer = SensorMLTrainer(sensor_type)
        metrics = trainer.train_all(days=days)
        trainer.close()
        
        if not metrics:
            return jsonify({'error': 'No se pudo entrenar el modelo'}), 500
        
        # Log de acción
        postgres_db.log_action(
            request.user['user_id'],
            'TRAIN_MODEL',
            f'predictions/{sensor_type}/train',
            f'days={days}'
        )
        
        return jsonify({
            'message': 'Modelo entrenado exitosamente',
            'sensor_type': sensor_type,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error entrenando modelo: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/train/all', methods=['POST'])
@token_required
def train_all_models():
    """
    Entrenar todos los modelos (solo admins)
    """
    try:
        # Solo admins
        if 'admin' not in request.user['role']:
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        data = request.get_json() or {}
        days = data.get('days', 60)
        
        results = {}
        
        for sensor_type in Config.SENSOR_TYPES:
            trainer = SensorMLTrainer(sensor_type)
            metrics = trainer.train_all(days=days)
            trainer.close()
            
            results[sensor_type] = {
                'success': metrics is not None,
                'metrics': metrics
            }
        
        # Log de acción
        postgres_db.log_action(
            request.user['user_id'],
            'TRAIN_ALL_MODELS',
            'predictions/train/all',
            f'days={days}'
        )
        
        return jsonify({
            'message': 'Entrenamiento completado',
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error entrenando modelos: {e}")
        return jsonify({'error': str(e)}), 500