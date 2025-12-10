"""
Consumer Kafka - Consume mensajes de Kafka y los guarda en MongoDB
"""
import json
import logging
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from pymongo import MongoClient, ASCENDING
from datetime import datetime
from src.config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaMongoConsumer:
    """Consumidor que lee de Kafka y guarda en MongoDB"""
    
    def __init__(self):
        """Inicializar consumidor y conexión a MongoDB"""
        self.consumer = None
        self.mongo_client = None
        self.db = None
        self.connect_mongodb()
        self.connect_kafka()
    
    def connect_mongodb(self):
        """Conectar a MongoDB"""
        try:
            self.mongo_client = MongoClient(Config.MONGODB_URI)
            self.db = self.mongo_client[Config.MONGODB_DATABASE]
            
            # Crear índices para mejor rendimiento
            for sensor_type in Config.SENSOR_TYPES:
                collection_name = Config.get_mongodb_collection(sensor_type)
                collection = self.db[collection_name]
                
                # Índice en timestamp
                collection.create_index([("time", ASCENDING)])
                collection.create_index([("deviceInfo.deviceName", ASCENDING)])
                
            logger.info(f"✓ Conectado a MongoDB: {Config.MONGODB_DATABASE}")
        except Exception as e:
            logger.error(f"✗ Error conectando a MongoDB: {e}")
            raise
    
    def connect_kafka(self):
        """Conectar a Kafka como consumidor"""
        try:
            topics = list(Config.KAFKA_TOPICS.values())
            
            self.consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=Config.KAFKA_CONSUMER_GROUP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_records=100
            )
            
            logger.info(f"✓ Consumidor Kafka conectado")
            logger.info(f"  Topics: {topics}")
            logger.info(f"  Group: {Config.KAFKA_CONSUMER_GROUP}")
        except Exception as e:
            logger.error(f"✗ Error conectando consumidor Kafka: {e}")
            raise
    
    def get_collection_for_topic(self, topic):
        """
        Obtener colección de MongoDB según el topic
        
        Args:
            topic: Nombre del topic de Kafka
            
        Returns:
            Colección de MongoDB y tipo de sensor
        """
        for sensor_type, topic_name in Config.KAFKA_TOPICS.items():
            if topic == topic_name:
                collection_name = Config.get_mongodb_collection(sensor_type)
                return self.db[collection_name], sensor_type
        return None, None
    
    def transform_data(self, data, sensor_type):
        """
        Transformar datos antes de guardar en MongoDB
        
        Args:
            data: Datos originales
            sensor_type: Tipo de sensor
            
        Returns:
            Datos transformados
        """
        # Agregar metadatos
        data['processed_at'] = datetime.utcnow()
        data['sensor_type'] = sensor_type
        
        # Convertir campos numéricos
        numeric_fields = {
            'aire': ['object.co2', 'object.temperature', 'object.humidity', 
                    'object.pressure', 'object.battery'],
            'sonido': ['object.LAeq', 'object.LAI', 'object.LAImax', 'object.battery'],
            'soterrado': ['object.distance', 'object.battery']
        }
        
        if sensor_type in numeric_fields:
            for field in numeric_fields[sensor_type]:
                if field in data and data[field] is not None:
                    try:
                        data[field] = float(data[field])
                    except (ValueError, TypeError):
                        pass
        
        return data
    
    def save_to_mongodb(self, collection, data):
        """
        Guardar datos en MongoDB
        
        Args:
            collection: Colección de MongoDB
            data: Datos a guardar
            
        Returns:
            ID del documento insertado
        """
        try:
            # Verificar que la colección no sea None
            if collection is None:
                logger.error("Colección no válida para guardar datos")
                return None
                
            result = collection.insert_one(data)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error guardando en MongoDB: {e}")
            return None
    
    def is_connected(self):
        """
        Verificar si todas las conexiones están activas
        
        Returns:
            bool: True si todas las conexiones están activas
        """
        return (
            self.mongo_client is not None and 
            self.db is not None and
            self.consumer is not None
        )
    
    def consume_messages(self):
        """Consumir mensajes de Kafka continuamente"""
        # Verificar conexiones usando 'is None' en lugar de 'not'
        if self.consumer is None:
            logger.error("Consumidor Kafka no inicializado")
            return
        
        if self.db is None:
            logger.error("Conexión MongoDB no inicializada")
            return
        
        logger.info("\n🚀 Iniciando consumo de mensajes...")
        logger.info("Presione Ctrl+C para detener\n")
        
        message_count = 0
        error_count = 0
        
        try:
            for message in self.consumer:
                try:
                    # Obtener colección según topic
                    collection, sensor_type = self.get_collection_for_topic(message.topic)
                    
                    # Verificar usando 'is None' para PyMongo 4.0+
                    if collection is None:
                        logger.warning(f"Topic desconocido: {message.topic}")
                        error_count += 1
                        continue
                    
                    if sensor_type is None:
                        logger.warning(f"No se pudo determinar tipo de sensor para topic: {message.topic}")
                        error_count += 1
                        continue
                    
                    # Transformar datos
                    data = self.transform_data(message.value, sensor_type)
                    
                    # Guardar en MongoDB
                    doc_id = self.save_to_mongodb(collection, data)
                    
                    if doc_id:
                        message_count += 1
                        
                        if message_count % 10 == 0:
                            logger.info(f"✓ Procesados: {message_count} mensajes (Errores: {error_count})")
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error procesando mensaje: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("\n⚠ Deteniendo consumidor...")
        except Exception as e:
            logger.error(f"Error inesperado en consumo: {e}")
        finally:
            self.close()
            logger.info(f"""
            Resumen:
            - Mensajes procesados exitosamente: {message_count}
            - Errores encontrados: {error_count}
            - Tasa de éxito: {message_count/(message_count+error_count)*100:.1f}% 
              si message_count+error_count > 0 else 0%
            """)
    
    def close(self):
        """Cerrar conexiones"""
        if self.consumer is not None:
            try:
                self.consumer.close()
                logger.info("✓ Consumidor Kafka cerrado")
            except Exception as e:
                logger.error(f"Error cerrando consumidor Kafka: {e}")
        
        if self.mongo_client is not None:
            try:
                self.mongo_client.close()
                logger.info("✓ Conexión MongoDB cerrada")
            except Exception as e:
                logger.error(f"Error cerrando conexión MongoDB: {e}")


def main():
    """Función principal"""
    print("="*60)
    print(" CONSUMIDOR KAFKA → MONGODB ".center(60))
    print("="*60)
    print(f"\nKafka: {Config.KAFKA_BOOTSTRAP_SERVERS}")
    print(f"MongoDB: {Config.MONGODB_DATABASE}")
    print(f"Topics: {list(Config.KAFKA_TOPICS.values())}")
    print("\n" + "="*60)
    
    try:
        consumer = KafkaMongoConsumer()
        
        # Verificar que todo esté conectado
        if consumer.is_connected():
            consumer.consume_messages()
        else:
            logger.error("No se pudo establecer todas las conexiones necesarias")
            
    except Exception as e:
        logger.error(f"Error inicializando el consumidor: {e}")
        return


if __name__ == "__main__":
    main()