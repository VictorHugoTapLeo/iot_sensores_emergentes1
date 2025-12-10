# Guia de Inicio Rapido - Windows

## Servicios Iniciados

- Kafka: localhost:9092
- MongoDB: localhost:27017
- PostgreSQL: localhost:5432

## Proximos Pasos

1. Activar entorno virtual:
   venv\Scripts\activate.bat

2. Generar datos:
   python simulador_sensores.py

3. Enviar a Kafka:
   python -m src.data_ingestion.csv_producer

4. Consumir datos (nueva terminal):
   python -m src.data_ingestion.kafka_consumer

5. Entrenar ML:
   python -m src.ml.trainer

6. Iniciar API:
   python -m src.api.app

7. Abrir navegador:
   start frontend\index.html

## Comandos Utiles

Ver logs: docker-compose logs -f
Detener: docker-compose down
Reiniciar: docker-compose restart
