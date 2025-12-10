#!/usr/bin/env python3
"""
Script para entrenar modelos con TODOS los datos disponibles
Sin importar las fechas
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml.trainer import SensorMLTrainer
from src.config.settings import Config
from src.database.mongodb_manager import MongoDBManager

def main():
    print("="*60)
    print(" ENTRENAMIENTO CON TODOS LOS DATOS ".center(60))
    print("="*60)
    
    # Verificar datos disponibles
    print("\nVerificando datos disponibles...")
    db = MongoDBManager()
    
    total_data = {}
    for sensor_type in Config.SENSOR_TYPES:
        count = db.count_documents(sensor_type)
        total_data[sensor_type] = count
        print(f"  {sensor_type.capitalize()}: {count} registros")
    
    db.close()
    
    if all(count == 0 for count in total_data.values()):
        print("\n✗ No hay datos en MongoDB")
        print("  Ejecute: python -m src.data_ingestion.csv_producer")
        return
    
    print("\n" + "="*60)
    print("Este script entrenará modelos usando TODOS los datos")
    print("disponibles, sin importar las fechas.")
    print("="*60)
    
    confirm = input("\n¿Continuar? (s/n): ").strip().lower()
    if confirm != 's':
        print("Cancelado.")
        return
    
    # Entrenar cada sensor
    for sensor_type in Config.SENSOR_TYPES:
        if total_data[sensor_type] < 50:
            print(f"\n⚠ Saltando {sensor_type}: datos insuficientes ({total_data[sensor_type]} < 50)")
            continue
        
        print(f"\n{'='*60}")
        print(f" ENTRENANDO {sensor_type.upper()} ".center(60))
        print(f"{'='*60}")
        
        try:
            trainer = SensorMLTrainer(sensor_type)
            
            # Usar days=0 para cargar todos los datos
            metrics = trainer.train_all(days=0)
            
            if metrics:
                print(f"\n✓ Modelos entrenados para {sensor_type}")
                
                # Mostrar métricas
                for field, metric in metrics.items():
                    r2_score = metric['test_r2'] * 100
                    quality = "Excelente" if r2_score >= 85 else "Bueno" if r2_score >= 70 else "Mejorar"
                    
                    print(f"\n  {field}:")
                    print(f"    R²: {r2_score:.2f}% ({quality})")
                    print(f"    RMSE: {metric['test_rmse']:.2f}")
                    print(f"    MAE: {metric['test_mae']:.2f}")
                    print(f"    Muestras: {metric['samples']}")
            else:
                print(f"\n✗ No se pudo entrenar {sensor_type}")
            
            trainer.close()
            
        except Exception as e:
            print(f"\n✗ Error entrenando {sensor_type}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(" ENTRENAMIENTO COMPLETADO ".center(60))
    print("="*60)
    
    # Verificar modelos creados
    print("\nModelos creados:")
    for sensor_type in Config.SENSOR_TYPES:
        models_path = Config.ML_MODELS_PATH / sensor_type
        if models_path.exists():
            model_files = list(models_path.glob("*.joblib"))
            print(f"  {sensor_type.capitalize()}: {len(model_files)} archivos")
        else:
            print(f"  {sensor_type.capitalize()}: 0 archivos")
    
    print("\n✓ Ahora puede generar predicciones en el frontend")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Entrenamiento cancelado")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()