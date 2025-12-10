"""
MongoDB Manager - Gestor de operaciones con MongoDB
"""
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
from src.config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBManager:
    """Gestor de operaciones con MongoDB"""
    
    def __init__(self):
        """Inicializar conexión a MongoDB"""
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DATABASE]
        logger.info(f"✓ MongoDB Manager inicializado: {Config.MONGODB_DATABASE}")
    
    def get_collection(self, sensor_type):
        """Obtener colección por tipo de sensor"""
        collection_name = Config.get_mongodb_collection(sensor_type)
        return self.db[collection_name]
    
    def get_latest_data(self, sensor_type, limit=100):
        """
        Obtener últimos N registros de un sensor
        
        Args:
            sensor_type: Tipo de sensor
            limit: Cantidad de registros
            
        Returns:
            Lista de documentos
        """
        try:
            collection = self.get_collection(sensor_type)
            cursor = collection.find().sort("time", DESCENDING).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error obteniendo últimos datos: {e}")
            return []
    
    def get_data_by_date_range(self, sensor_type, start_date, end_date):
        """
        Obtener datos en un rango de fechas
        
        Args:
            sensor_type: Tipo de sensor
            start_date: Fecha inicio (string ISO o datetime)
            end_date: Fecha fin (string ISO o datetime)
            
        Returns:
            Lista de documentos
        """
        try:
            collection = self.get_collection(sensor_type)
            
            # Convertir a datetime si son strings
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            query = {
                "time": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }
            
            cursor = collection.find(query).sort("time", ASCENDING)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error obteniendo datos por rango: {e}")
            return []
    
    def get_data_for_ml_training(self, sensor_type, days=30):
        """
        Obtener datos para entrenamiento de ML
        
        Args:
            sensor_type: Tipo de sensor
            days: Días hacia atrás
            
        Returns:
            Lista de documentos
        """
        try:
            collection = self.get_collection(sensor_type)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = {
                "time": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }
            
            cursor = collection.find(query).sort("time", ASCENDING)
            data = list(cursor)
            logger.info(f"Datos para ML ({sensor_type}): {len(data)} registros")
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos para ML: {e}")
            return []
    
    def get_statistics(self, sensor_type, hours=24):
        """
        Obtener estadísticas de las últimas N horas
        
        Args:
            sensor_type: Tipo de sensor
            hours: Horas hacia atrás
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            collection = self.get_collection(sensor_type)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Campos según tipo de sensor
            fields_map = {
                'aire': ['object.co2', 'object.temperature', 'object.humidity', 'object.pressure'],
                'sonido': ['object.LAeq', 'object.LAI', 'object.LAImax'],
                'soterrado': ['object.distance']
            }
            
            fields = fields_map.get(sensor_type, [])
            
            pipeline = [
                {
                    "$match": {
                        "time": {"$gte": cutoff_time.isoformat()}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "count": {"$sum": 1},
                        **{
                            f"{field}_avg": {"$avg": f"${field}"}
                            for field in fields
                        },
                        **{
                            f"{field}_min": {"$min": f"${field}"}
                            for field in fields
                        },
                        **{
                            f"{field}_max": {"$max": f"${field}"}
                            for field in fields
                        }
                    }
                }
            ]
            
            result = list(collection.aggregate(pipeline))
            return result[0] if result else {}
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {e}")
            return {}
    
    def get_device_list(self, sensor_type):
        """
        Obtener lista de dispositivos únicos
        
        Args:
            sensor_type: Tipo de sensor
            
        Returns:
            Lista de nombres de dispositivos
        """
        try:
            collection = self.get_collection(sensor_type)
            devices = collection.distinct("deviceInfo.deviceName")
            return devices
        except Exception as e:
            logger.error(f"Error obteniendo lista de dispositivos: {e}")
            return []
    
    def save_prediction(self, sensor_type, prediction_data):
        """
        Guardar predicción en MongoDB
        
        Args:
            sensor_type: Tipo de sensor
            prediction_data: Datos de la predicción
            
        Returns:
            ID del documento insertado
        """
        try:
            collection = self.db[Config.MONGODB_COLLECTIONS['predictions']]
            
            document = {
                'sensor_type': sensor_type,
                'created_at': datetime.utcnow(),
                'predictions': prediction_data
            }
            
            result = collection.insert_one(document)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error guardando predicción: {e}")
            return None
    
    def get_latest_prediction(self, sensor_type):
        """
        Obtener última predicción guardada
        
        Args:
            sensor_type: Tipo de sensor
            
        Returns:
            Documento de predicción
        """
        try:
            collection = self.db[Config.MONGODB_COLLECTIONS['predictions']]
            
            result = collection.find_one(
                {'sensor_type': sensor_type},
                sort=[('created_at', DESCENDING)]
            )
            
            return result
        except Exception as e:
            logger.error(f"Error obteniendo predicción: {e}")
            return None
    
    def count_documents(self, sensor_type):
        """Contar documentos en colección"""
        try:
            collection = self.get_collection(sensor_type)
            return collection.count_documents({})
        except Exception as e:
            logger.error(f"Error contando documentos: {e}")
            return 0
    
    def close(self):
        """Cerrar conexión"""
        if self.client:
            self.client.close()
            logger.info("✓ Conexión MongoDB cerrada")