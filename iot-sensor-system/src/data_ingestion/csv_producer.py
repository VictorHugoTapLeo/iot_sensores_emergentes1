"""
Producer Kafka - Lee datos CSV y los envía a Kafka
"""
import csv
import json
import time
import logging
from pathlib import Path
from kafka import KafkaProducer
from kafka.errors import KafkaError
from src.config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVKafkaProducer:
    """Productor que lee CSV y envía datos a Kafka"""
    
    def __init__(self):
        """Inicializar productor Kafka"""
        self.producer = None
        self.connect()
    
    def connect(self):
        """Conectar a Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"✓ Conectado a Kafka: {Config.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"✗ Error conectando a Kafka: {e}")
            raise
    
    def read_csv_file(self, filepath):
        """
        Leer archivo CSV y retornar lista de registros
        
        Args:
            filepath: Ruta al archivo CSV
            
        Returns:
            Lista de diccionarios con los datos
        """
        records = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
            logger.info(f"✓ Leídos {len(records)} registros de {filepath}")
            return records
        except Exception as e:
            logger.error(f"✗ Error leyendo CSV {filepath}: {e}")
            return []
    
    def detect_sensor_type(self, filepath):
        """
        Detectar tipo de sensor por el nombre del archivo
        
        Args:
            filepath: Ruta al archivo
            
        Returns:
            Tipo de sensor ('aire', 'sonido', 'soterrado')
        """
        filename = Path(filepath).name.lower()
        
        if 'aire' in filename:
            return 'aire'
        elif 'sonido' in filename:
            return 'sonido'
        elif 'soterrado' in filename:
            return 'soterrado'
        else:
            logger.warning(f"Tipo de sensor no detectado para: {filename}")
            return None
    
    def send_to_kafka(self, sensor_type, records, interval=None):
        """
        Enviar registros a Kafka
        
        Args:
            sensor_type: Tipo de sensor
            records: Lista de registros
            interval: Tiempo de espera entre envíos (segundos)
        """
        if not self.producer:
            logger.error("Productor no conectado")
            return
        
        topic = Config.get_kafka_topic(sensor_type)
        if not topic:
            logger.error(f"Topic no encontrado para sensor: {sensor_type}")
            return
        
        interval = interval or Config.KAFKA_SEND_INTERVAL
        sent_count = 0
        failed_count = 0
        
        logger.info(f"Enviando {len(records)} registros al topic '{topic}'...")
        
        for idx, record in enumerate(records, 1):
            try:
                # Agregar metadatos
                record['sensor_type'] = sensor_type
                record['kafka_timestamp'] = time.time()
                
                # Enviar a Kafka
                future = self.producer.send(topic, value=record)
                future.get(timeout=10)
                
                sent_count += 1
                
                if idx % 100 == 0:
                    logger.info(f"Progreso: {idx}/{len(records)} registros enviados")
                
                # Pausa entre envíos
                time.sleep(interval)
                
            except KafkaError as e:
                logger.error(f"Error Kafka enviando registro {idx}: {e}")
                failed_count += 1
            except Exception as e:
                logger.error(f"Error general enviando registro {idx}: {e}")
                failed_count += 1
        
        # Flush final
        self.producer.flush()
        
        logger.info(f"""
        Resumen de envío:
        - Topic: {topic}
        - Enviados: {sent_count}
        - Fallidos: {failed_count}
        - Total: {len(records)}
        """)
    
    def process_csv_files(self, csv_files, interval=None):
        """
        Procesar múltiples archivos CSV
        
        Args:
            csv_files: Lista de rutas a archivos CSV
            interval: Intervalo entre envíos
        """
        for csv_file in csv_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Procesando: {csv_file}")
            logger.info(f"{'='*60}")
            
            # Detectar tipo de sensor
            sensor_type = self.detect_sensor_type(csv_file)
            if not sensor_type:
                logger.warning(f"Saltando archivo: {csv_file}")
                continue
            
            # Leer CSV
            records = self.read_csv_file(csv_file)
            if not records:
                continue
            
            # Enviar a Kafka
            self.send_to_kafka(sensor_type, records, interval)
    
    def close(self):
        """Cerrar conexión"""
        if self.producer:
            self.producer.close()
            logger.info("✓ Productor cerrado")


def main():
    """Función principal para ejecutar el productor"""
    import sys
    import glob
    
    print("="*60)
    print(" PRODUCTOR KAFKA - CSV TO KAFKA ".center(60))
    print("="*60)
    
    # Buscar archivos CSV
    data_path = Config.DATA_PATH
    csv_pattern = str(data_path / "simulacion_*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print(f"\n✗ No se encontraron archivos CSV en: {data_path}")
        print(f"  Patrón buscado: simulacion_*.csv")
        sys.exit(1)
    
    print(f"\n✓ Archivos CSV encontrados: {len(csv_files)}")
    for f in csv_files:
        print(f"  - {Path(f).name}")
    
    # Configuración
    print("\nConfiguración:")
    print(f"  - Kafka: {Config.KAFKA_BOOTSTRAP_SERVERS}")
    print(f"  - Intervalo: {Config.KAFKA_SEND_INTERVAL}s por registro")
    
    confirm = input("\n¿Desea continuar? (s/n): ").strip().lower()
    if confirm != 's':
        print("Operación cancelada.")
        sys.exit(0)
    
    # Procesar archivos
    producer = CSVKafkaProducer()
    try:
        producer.process_csv_files(csv_files)
    except KeyboardInterrupt:
        print("\n\n⚠ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        producer.close()
    
    print("\n" + "="*60)
    print(" PROCESO COMPLETADO ".center(60))
    print("="*60)


if __name__ == "__main__":
    main()