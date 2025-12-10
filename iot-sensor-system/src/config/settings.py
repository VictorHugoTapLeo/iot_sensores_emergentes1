"""
Configuración centralizada del sistema IoT
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

class Config:
    """Configuración base del sistema"""
    
    # Paths
    BASE_DIR = BASE_DIR
    DATA_PATH = BASE_DIR / 'data'
    ML_MODELS_PATH = BASE_DIR / 'src' / 'ml' / 'models'
    LOGS_PATH = BASE_DIR / 'logs'
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPICS = {
        'aire': os.getenv('KAFKA_TOPIC_AIRE', 'sensor-aire'),
        'sonido': os.getenv('KAFKA_TOPIC_SONIDO', 'sensor-sonido'),
        'soterrado': os.getenv('KAFKA_TOPIC_SOTERRADO', 'sensor-soterrado')
    }
    KAFKA_CONSUMER_GROUP = os.getenv('KAFKA_CONSUMER_GROUP', 'iot-consumers')
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://admin:admin123@localhost:27017/')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'iot_sensors')
    MONGODB_COLLECTIONS = {
        'aire': os.getenv('MONGODB_COLLECTION_AIRE', 'datos_aire'),
        'sonido': os.getenv('MONGODB_COLLECTION_SONIDO', 'datos_sonido'),
        'soterrado': os.getenv('MONGODB_COLLECTION_SOTERRADO', 'datos_soterrado'),
        'predictions': 'predicciones',
        'logs': 'system_logs'
    }
    
    # PostgreSQL
    POSTGRES_CONFIG = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'iot_system'),
        'user': os.getenv('POSTGRES_USER', 'admin'),
        'password': os.getenv('POSTGRES_PASSWORD', 'admin123')
    }
    
    # Redis
    REDIS_CONFIG = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 0))
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    
    # API
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    API_DEBUG = os.getenv('API_DEBUG', 'True').lower() == 'true'
    
    # Machine Learning
    ML_PREDICTION_DAYS = {
        'short': int(os.getenv('ML_PREDICTION_DAYS_SHORT', 7)),
        'long': int(os.getenv('ML_PREDICTION_DAYS_LONG', 30))
    }
    
    # Data Ingestion
    CSV_BATCH_SIZE = int(os.getenv('CSV_BATCH_SIZE', 100))
    KAFKA_SEND_INTERVAL = float(os.getenv('KAFKA_SEND_INTERVAL', 0.1))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Roles de usuario
    ROLES = {
        'ALCALDE': 'ejecutivo_alcalde',
        'DIRECTOR': 'ejecutivo_director',
        'ADMIN': 'operativo_admin',
        'USER': 'operativo_user'
    }
    
    # Tipos de sensores
    SENSOR_TYPES = ['aire', 'sonido', 'soterrado']
    
    @classmethod
    def init_directories(cls):
        """Crear directorios necesarios"""
        cls.DATA_PATH.mkdir(exist_ok=True)
        cls.ML_MODELS_PATH.mkdir(parents=True, exist_ok=True)
        cls.LOGS_PATH.mkdir(exist_ok=True)
    
    @classmethod
    def get_kafka_topic(cls, sensor_type):
        """Obtener topic de Kafka por tipo de sensor"""
        return cls.KAFKA_TOPICS.get(sensor_type.lower())
    
    @classmethod
    def get_mongodb_collection(cls, sensor_type):
        """Obtener colección de MongoDB por tipo de sensor"""
        return cls.MONGODB_COLLECTIONS.get(sensor_type.lower())

# Inicializar directorios al importar
Config.init_directories()