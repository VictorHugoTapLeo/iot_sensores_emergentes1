#!/usr/bin/env python3
"""
Simulador de Sensores IoT con Patrones Temporales
Genera datos con tendencias y ciclos para Machine Learning
"""

import csv
import random
import uuid
import math
from datetime import datetime, timedelta
import sys

class SimuladorSensoresML:
    def __init__(self):
        # Configuración común
        self.tenant_name = "Secretaria de ciudad digital y gobierno electronico"
        self.tenant_id = "52f14cd4-c6f1-4fbd-8f87-4025e1d49242"
        
        # Configuración de sensores (usar primero de cada tipo)
        self.sensores_config = {
            'aire': {
                'device_name': 'EMS-6500',
                'app_name': 'EM500-CO2-915M',
                'dev_eui': '24e124126d376500',
                'profile_name': 'EM500-CO2-915M',
                'profile_id': '1d9d2a0d-d5c2-4339-9080-8a9defc094a0',
                'app_id': '572beadb-725b-4d67-a009-e9ca93cc5fc3',
                'description': 'Mide CO2, temperatura, humedad y presión',
                'address': 'Cristo de la Concordia',
                'name': 'Sensor CO2',
                'location': '-17.3844962748556, -66.1353062672603',
                'dev_addr': '01f5c500',
                'fport': 85
            },
            'sonido': {
                'device_name': 'SLS-2648',
                'app_name': 'WS302-915M',
                'dev_eui': '24e124743d012648',
                'profile_name': 'WS302-915M',
                'profile_id': '19da3dff-9fe0-41ed-8c8e-fb5a7017d025',
                'app_id': 'bb9914a5-1c77-4941-9baf-1332dc8b2d40',
                'description': 'Mide decibeles (dB)',
                'address': 'Av. Melchor Urquidi',
                'name': 'Sensor de sonido',
                'location': '-17.375344862040876, -66.14936933868707',
                'dev_addr': '008ac648',
                'fport': 85
            },
            'soterrado': {
                'device_name': 'UDS-6632',
                'app_name': 'EM310-UDL-915M',
                'dev_eui': '24e124713d396632',
                'profile_name': 'EM310-UDL-915M',
                'profile_id': '6a273702-1701-450e-a5ce-2757bbee4165',
                'app_id': 'ab61f3b6-fb26-4bbb-aeff-332097b89aab',
                'description': 'Mide nivel de agua',
                'address': 'Parque Excombatientes',
                'name': 'Sensor nivel de liquido',
                'location': '-17.385320458924163, -66.17390941117199',
                'dev_addr': '010fa632',
                'fport': 85
            }
        }
    
    def generar_datos_aire_con_patron(self, timestamp_idx, total_registros):
        """Genera datos de aire con patrones temporales realistas"""
        
        # Hora del día (0-23)
        hora = timestamp_idx % 24
        # Día de la semana (0-6)
        dia_semana = (timestamp_idx // 24) % 7
        
        # CO2: Mayor en horas laborales, menor en la noche
        co2_base = 600
        co2_variacion_hora = 200 * math.sin((hora - 6) * math.pi / 12)  # Pico a las 12-14h
        co2_variacion_dia = 50 if dia_semana < 5 else -50  # Más CO2 en días laborales
        co2 = max(400, co2_base + co2_variacion_hora + co2_variacion_dia + random.uniform(-50, 50))
        
        # Temperatura: Sigue ciclo diario
        temp_base = 20
        temp_variacion = 7 * math.sin((hora - 6) * math.pi / 12)  # Pico a mediodía
        temperatura = temp_base + temp_variacion + random.uniform(-2, 2)
        
        # Humedad: Inversa a temperatura
        humedad_base = 60
        humedad = max(30, min(90, humedad_base - (temperatura - 20) * 2 + random.uniform(-5, 5)))
        
        # Presión: Variación lenta (tendencia)
        presion_base = 1000
        presion_tendencia = 20 * math.sin(timestamp_idx * 2 * math.pi / total_registros)
        presion = presion_base + presion_tendencia + random.uniform(-5, 5)
        
        bateria = round(random.uniform(90, 100), 1)
        
        # Determinar estados
        co2_status = "Normal" if co2 < 800 else "Moderado" if co2 < 1000 else "Alto"
        temp_status = "Frio" if temperatura < 18 else "Normal" if temperatura < 25 else "Calido"
        hum_status = "Bajo" if humedad < 40 else "Normal" if humedad < 70 else "Alto"
        pres_status = "Bajo" if presion < 990 else "Normal" if presion < 1010 else "Alto"
        
        return {
            'object.co2': round(co2, 1),
            'object.co2_status': co2_status,
            'object.co2_message': f"CO2: {round(co2, 1)} ppm",
            'object.temperature': round(temperatura, 1),
            'object.temperature_status': temp_status,
            'object.temperature_message': f"Temperatura: {round(temperatura, 1)}°C",
            'object.humidity': round(humedad, 1),
            'object.humidity_status': hum_status,
            'object.humidity_message': f"Humedad: {round(humedad, 1)}%",
            'object.pressure': round(presion, 1),
            'object.pressure_status': pres_status,
            'object.pressure_message': f"Presión: {round(presion, 1)} hPa",
            'object.battery': bateria
        }
    
    def generar_datos_sonido_con_patron(self, timestamp_idx, total_registros):
        """Genera datos de sonido con patrones temporales"""
        
        hora = timestamp_idx % 24
        dia_semana = (timestamp_idx // 24) % 7
        
        # Sonido: Mayor en horas pico (7-9h, 18-20h), menor en la noche
        if 7 <= hora <= 9 or 18 <= hora <= 20:
            laeq_base = 75
        elif 22 <= hora or hora <= 6:
            laeq_base = 50
        else:
            laeq_base = 65
        
        # Más ruido en días laborales
        laeq_ajuste = 5 if dia_semana < 5 else -3
        
        laeq = laeq_base + laeq_ajuste + random.uniform(-5, 5)
        lai = laeq + random.uniform(-3, 3)
        laimax = laeq + random.uniform(10, 20)
        bateria = round(random.uniform(90, 100), 1)
        
        status = "Normal" if laeq < 60 else "Moderado" if laeq < 75 else "Alto"
        
        return {
            'object.LAeq': round(laeq, 1),
            'object.LAI': round(lai, 1),
            'object.LAImax': round(laimax, 1),
            'object.battery': bateria,
            'object.status': status
        }
    
    def generar_datos_soterrado_con_patron(self, timestamp_idx, total_registros):
        """Genera datos de nivel de líquido con patrón de consumo"""
        
        hora = timestamp_idx % 24
        
        # Consumo de agua: Mayor en horas pico
        if 6 <= hora <= 9 or 18 <= hora <= 21:
            # Horas pico: nivel baja (distancia aumenta)
            distancia_base = 80
        else:
            # Otras horas: nivel estable o se llena
            distancia_base = 50
        
        # Tendencia de llenado gradual durante el día
        tendencia = -20 * math.sin(hora * math.pi / 24)
        
        distancia = max(20, min(150, distancia_base + tendencia + random.uniform(-10, 10)))
        bateria = round(random.uniform(85, 100), 1)
        
        if distancia < 50:
            status = "Lleno"
            posicion = "normal"
        elif distancia < 100:
            status = "Medio"
            posicion = "normal"
        else:
            status = "Bajo"
            posicion = "normal"
        
        return {
            'object.distance': round(distancia, 1),
            'object.position': posicion,
            'object.battery': bateria,
            'object.status': status
        }
    
    def generar_campos_comunes(self, sensor_type, timestamp, fcnt, config):
        """Genera campos comunes para todos los sensores"""
        
        return {
            '_id': str(uuid.uuid4().hex[:24]),
            'devAddr': config['dev_addr'],
            'deduplicationId': str(uuid.uuid4()),
            'time': timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+00:00',
            'deviceInfo.deviceClassEnabled': 'CLASS_A',
            'deviceInfo.tenantName': self.tenant_name,
            'deviceInfo.tenantId': self.tenant_id,
            'deviceInfo.deviceProfileId': config['profile_id'],
            'deviceInfo.applicationId': config['app_id'],
            'deviceInfo.deviceName': config['device_name'],
            'deviceInfo.applicationName': config['app_name'],
            'deviceInfo.devEui': config['dev_eui'],
            'deviceInfo.deviceProfileName': config['profile_name'],
            'deviceInfo.tags.Description': config['description'],
            'deviceInfo.tags.Address': config['address'],
            'deviceInfo.tags.Name': config['name'],
            'deviceInfo.tags.Location': config['location'],
            'txInfo.modulation.lora.spreadingFactor': 10,
            'txInfo.modulation.lora.bandwidth': 125000,
            'txInfo.modulation.lora.codeRate': 'CR_4_5',
            'txInfo.frequency': 915200000,
            'fPort': config['fport'],
            'data': '/wv//wEB',
            'fCnt': fcnt,
            'confirmed': 'FALSE',
            'adr': 'TRUE',
            'dr': 2,
            'rxInfo[0].rssi': random.randint(-110, -85),
            'rxInfo[1].rssi': random.randint(-110, -85),
            'rxInfo[2].rssi': random.randint(-110, -85),
            'rxInfo[0].snr': round(random.uniform(-5, 8), 1),
            'rxInfo[1].snr': round(random.uniform(-5, 8), 1),
            'rxInfo[2].snr': round(random.uniform(-5, 8), 1),
            'rxInfo[0].metadata.region_config_id': 'au915_0',
            'rxInfo[1].metadata.region_config_id': 'au915_0',
            'rxInfo[2].metadata.region_config_id': 'au915_0',
            'rxInfo[0].metadata.region_common_name': 'AU915',
            'rxInfo[1].metadata.region_common_name': 'AU915',
            'rxInfo[2].metadata.region_common_name': 'AU915',
            'rxInfo[0].crcStatus': 'CRC_OK',
            'rxInfo[1].crcStatus': 'CRC_OK',
            'rxInfo[2].crcStatus': 'CRC_OK',
        }
    
    def simular_sensor(self, sensor_type, num_lecturas, intervalo_horas=1):
        """Simula lecturas de sensores con patrones temporales"""
        
        lecturas = []
        
        # Fecha de inicio: Hace 30 días desde hoy
        fecha_inicio = datetime.now() - timedelta(days=30)
        timestamp_actual = fecha_inicio
        
        config = self.sensores_config[sensor_type]
        
        print(f"\nGenerando {num_lecturas} lecturas de {sensor_type} con patrones ML...")
        print(f"Fecha inicio: {fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Intervalo: {intervalo_horas} hora(s)")
        
        for i in range(num_lecturas):
            # Campos comunes
            registro = self.generar_campos_comunes(sensor_type, timestamp_actual, i + 1, config)
            
            # Datos específicos CON PATRONES
            if sensor_type == 'aire':
                datos_sensor = self.generar_datos_aire_con_patron(i, num_lecturas)
            elif sensor_type == 'sonido':
                datos_sensor = self.generar_datos_sonido_con_patron(i, num_lecturas)
            elif sensor_type == 'soterrado':
                datos_sensor = self.generar_datos_soterrado_con_patron(i, num_lecturas)
            
            registro.update(datos_sensor)
            lecturas.append(registro)
            
            # Incrementar timestamp
            timestamp_actual += timedelta(hours=intervalo_horas)
            
            if (i + 1) % 100 == 0:
                print(f"  Progreso: {i + 1}/{num_lecturas}")
        
        print(f"✓ Completado: {num_lecturas} registros")
        return lecturas
    
    def guardar_csv(self, lecturas, nombre_archivo):
        """Guarda las lecturas en un archivo CSV"""
        if not lecturas:
            print("No hay lecturas para guardar")
            return
        
        fieldnames = list(lecturas[0].keys())
        
        with open(nombre_archivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lecturas)
        
        print(f"✓ Archivo guardado: {nombre_archivo}")

def main():
    print("="*60)
    print(" SIMULADOR IoT CON PATRONES PARA ML ".center(60))
    print("="*60)
    print("\nEste simulador genera datos con patrones temporales")
    print("realistas para que el Machine Learning funcione mejor.")
    print("\nPatrones incluidos:")
    print("  • Ciclos diarios (temperatura, CO2, sonido)")
    print("  • Diferencias entre días laborales/fines de semana")
    print("  • Horas pico y horas valle")
    print("  • Tendencias a largo plazo")
    
    simulador = SimuladorSensoresML()
    
    print("\n" + "-"*60)
    num_lecturas = int(input("\n¿Cuántas lecturas por sensor? (recomendado: 500): ") or 500)
    intervalo = float(input("¿Intervalo en horas? (recomendado: 1): ") or 1)
    
    print("\n" + "="*60)
    print("Generando datos para TODOS los sensores...")
    print("="*60)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for sensor_type in ['aire', 'sonido', 'soterrado']:
        lecturas = simulador.simular_sensor(sensor_type, num_lecturas, intervalo)
        nombre_archivo = f"data/simulacion_{sensor_type}_ml_{timestamp}.csv"
        simulador.guardar_csv(lecturas, nombre_archivo)
    
    print("\n" + "="*60)
    print(" ✓ GENERACIÓN COMPLETADA ".center(60))
    print("="*60)
    print("\nPróximos pasos:")
    print("  1. Enviar a Kafka: python -m src.data_ingestion.csv_producer")
    print("  2. Entrenar modelos: python scripts/train_all_data.py")
    print("  3. Generar predicciones en el frontend")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Simulación cancelada")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)