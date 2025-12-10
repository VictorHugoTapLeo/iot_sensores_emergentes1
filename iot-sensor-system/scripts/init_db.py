#!/usr/bin/env python3
"""
Script de inicialización de bases de datos
Crea tablas, índices y datos iniciales
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.mongodb_manager import MongoDBManager
from src.database.postgres_manager import PostgresManager
from src.config.settings import Config

def init_mongodb():
    """Inicializar MongoDB"""
    print("\n" + "="*60)
    print(" INICIALIZANDO MONGODB ".center(60))
    print("="*60)
    
    try:
        db = MongoDBManager()
        
        # Crear índices para cada colección
        for sensor_type in Config.SENSOR_TYPES:
            collection_name = Config.get_mongodb_collection(sensor_type)
            collection = db.db[collection_name]
            
            # Crear índices
            collection.create_index([("time", 1)])
            collection.create_index([("deviceInfo.deviceName", 1)])
            collection.create_index([("sensor_type", 1)])
            
            print(f"✓ Índices creados para: {collection_name}")
        
        # Crear colección de predicciones
        predictions_collection = db.db[Config.MONGODB_COLLECTIONS['predictions']]
        predictions_collection.create_index([("sensor_type", 1)])
        predictions_collection.create_index([("created_at", -1)])
        print(f"✓ Índices creados para: predicciones")
        
        # Mostrar estadísticas
        print("\nEstadísticas de colecciones:")
        for sensor_type in Config.SENSOR_TYPES:
            count = db.count_documents(sensor_type)
            print(f"  {sensor_type}: {count} documentos")
        
        db.close()
        print("\n✓ MongoDB inicializado correctamente")
        return True
        
    except Exception as e:
        print(f"\n✗ Error inicializando MongoDB: {e}")
        return False

def init_postgres():
    """Inicializar PostgreSQL"""
    print("\n" + "="*60)
    print(" INICIALIZANDO POSTGRESQL ".center(60))
    print("="*60)
    
    try:
        db = PostgresManager()
        
        # Las tablas ya se crean en __init__
        print("✓ Tablas creadas")
        
        # Verificar usuarios creados
        print("\nUsuarios del sistema:")
        users = [
            ('alcalde', Config.ROLES['ALCALDE']),
            ('director', Config.ROLES['DIRECTOR']),
            ('admin', Config.ROLES['ADMIN']),
            ('usuario', Config.ROLES['USER'])
        ]
        
        for username, role in users:
            user = db.get_user_by_username(username)
            if user:
                print(f"  ✓ {username} - {role}")
            else:
                print(f"  ✗ {username} - NO ENCONTRADO")
        
        db.close()
        print("\n✓ PostgreSQL inicializado correctamente")
        return True
        
    except Exception as e:
        print(f"\n✗ Error inicializando PostgreSQL: {e}")
        return False

def check_kafka():
    """Verificar conexión a Kafka"""
    print("\n" + "="*60)
    print(" VERIFICANDO KAFKA ".center(60))
    print("="*60)
    
    try:
        from kafka import KafkaAdminClient
        from kafka.admin import NewTopic
        
        admin_client = KafkaAdminClient(
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
            client_id='init_script'
        )
        
        # Crear topics si no existen
        topics = []
        for sensor_type in Config.SENSOR_TYPES:
            topic_name = Config.get_kafka_topic(sensor_type)
            topics.append(NewTopic(
                name=topic_name,
                num_partitions=1,
                replication_factor=1
            ))
        
        try:
            admin_client.create_topics(new_topics=topics, validate_only=False)
            print("✓ Topics de Kafka creados")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print("✓ Topics de Kafka ya existen")
            else:
                raise
        
        # Listar topics
        existing_topics = admin_client.list_topics()
        print("\nTopics disponibles:")
        for topic in existing_topics:
            print(f"  - {topic}")
        
        admin_client.close()
        print("\n✓ Kafka verificado correctamente")
        return True
        
    except Exception as e:
        print(f"\n✗ Error verificando Kafka: {e}")
        print("Asegúrese de que Kafka está ejecutándose:")
        print("  docker-compose up -d kafka")
        return False

def show_summary():
    """Mostrar resumen de configuración"""
    print("\n" + "="*60)
    print(" CONFIGURACIÓN DEL SISTEMA ".center(60))
    print("="*60)
    
    print(f"""
Kafka:
  Bootstrap Servers: {Config.KAFKA_BOOTSTRAP_SERVERS}
  Topics: {', '.join(Config.KAFKA_TOPICS.values())}

MongoDB:
  URI: {Config.MONGODB_URI.replace(Config.MONGODB_URI.split('@')[0].split('//')[1], '***')}
  Database: {Config.MONGODB_DATABASE}
  Colecciones: {', '.join(Config.MONGODB_COLLECTIONS.values())}

PostgreSQL:
  Host: {Config.POSTGRES_CONFIG['host']}:{Config.POSTGRES_CONFIG['port']}
  Database: {Config.POSTGRES_CONFIG['database']}
  User: {Config.POSTGRES_CONFIG['user']}

API:
  Host: {Config.API_HOST}
  Port: {Config.API_PORT}
  Debug: {Config.API_DEBUG}

Machine Learning:
  Models Path: {Config.ML_MODELS_PATH}
  Prediction Days: {Config.ML_PREDICTION_DAYS}
""")

def main():
    """Función principal"""
    print("="*60)
    print(" INICIALIZACIÓN DEL SISTEMA IoT GAMC ".center(60))
    print("="*60)
    
    results = {
        'mongodb': False,
        'postgres': False,
        'kafka': False
    }
    
    # Inicializar componentes
    results['mongodb'] = init_mongodb()
    results['postgres'] = init_postgres()
    results['kafka'] = check_kafka()
    
    # Mostrar configuración
    show_summary()
    
    # Resumen final
    print("\n" + "="*60)
    print(" RESUMEN DE INICIALIZACIÓN ".center(60))
    print("="*60)
    
    for component, status in results.items():
        status_str = "✓ OK" if status else "✗ ERROR"
        print(f"{component.upper()}: {status_str}")
    
    all_ok = all(results.values())
    
    if all_ok:
        print("\n✅ Sistema inicializado correctamente")
        print("\nPróximos pasos:")
        print("  1. Generar datos: python simulador_sensores.py")
        print("  2. Enviar a Kafka: python -m src.data_ingestion.csv_producer")
        print("  3. Consumir datos: python -m src.data_ingestion.kafka_consumer")
        print("  4. Entrenar ML: python -m src.ml.trainer")
        print("  5. Iniciar API: python -m src.api.app")
        print("  6. Abrir frontend/index.html")
    else:
        print("\n⚠️ Algunos componentes no se inicializaron correctamente")
        print("Verifique los errores arriba y corrija antes de continuar")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Inicialización cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)