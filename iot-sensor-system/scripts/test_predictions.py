#!/usr/bin/env python3
"""
Script para probar predicciones ML desde Python
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml.predictor import SensorMLPredictor
from src.ml.trainer import SensorMLTrainer
from src.database.mongodb_manager import MongoDBManager
from src.config.settings import Config

def check_data():
    """Verificar datos disponibles"""
    print("\n" + "="*60)
    print(" DATOS DISPONIBLES ".center(60))
    print("="*60)
    
    db = MongoDBManager()
    
    for sensor_type in Config.SENSOR_TYPES:
        count = db.count_documents(sensor_type)
        status = "✓" if count >= 50 else "⚠" if count > 0 else "✗"
        
        print(f"{status} {sensor_type.capitalize()}: {count} registros", end="")
        
        if count < 50:
            print(" (necesita al menos 50)")
        else:
            print(" (suficiente)")
    
    db.close()

def check_models():
    """Verificar modelos entrenados"""
    print("\n" + "="*60)
    print(" MODELOS ENTRENADOS ".center(60))
    print("="*60)
    
    for sensor_type in Config.SENSOR_TYPES:
        models_path = Config.ML_MODELS_PATH / sensor_type
        
        if not models_path.exists():
            print(f"✗ {sensor_type.capitalize()}: No hay carpeta de modelos")
            continue
        
        model_files = list(models_path.glob("*_model_*.joblib"))
        
        if model_files:
            print(f"✓ {sensor_type.capitalize()}: {len(model_files)} modelo(s)")
        else:
            print(f"✗ {sensor_type.capitalize()}: No hay modelos entrenados")

def test_prediction(sensor_type):
    """Probar predicción para un sensor"""
    print("\n" + "="*60)
    print(f" PROBANDO PREDICCIÓN - {sensor_type.upper()} ".center(60))
    print("="*60)
    
    try:
        predictor = SensorMLPredictor(sensor_type)
        
        if not predictor.models:
            print(f"✗ No hay modelos cargados para {sensor_type}")
            print("  Ejecute: python -m src.ml.trainer")
            return False
        
        print(f"✓ Modelos cargados: {len(predictor.models)}")
        
        # Generar predicción de prueba (7 días)
        print("\nGenerando predicción de 7 días...")
        predictions = predictor.predict(days=7, freq='D')
        
        if predictions:
            print("✓ Predicción exitosa")
            print(f"  Timestamps: {len(predictions['timestamps'])}")
            print(f"  Variables: {list(predictions['predictions'].keys())}")
            
            # Mostrar muestra
            for field, values in predictions['predictions'].items():
                print(f"\n  {field}:")
                print(f"    Primeros valores: {values[:3]}")
                print(f"    Promedio: {sum(values)/len(values):.2f}")
        else:
            print("✗ No se pudo generar predicción")
            return False
        
        predictor.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_training(sensor_type):
    """Probar entrenamiento para un sensor"""
    print("\n" + "="*60)
    print(f" PROBANDO ENTRENAMIENTO - {sensor_type.upper()} ".center(60))
    print("="*60)
    
    try:
        trainer = SensorMLTrainer(sensor_type)
        
        print("Entrenando con 60 días de datos...")
        metrics = trainer.train_all(days=60)
        
        if metrics:
            print("\n✓ Entrenamiento exitoso")
            
            for field, metric in metrics.items():
                r2_score = metric['test_r2']
                r2_percent = r2_score * 100
                
                status = "✓" if r2_score >= 0.85 else "⚠" if r2_score >= 0.70 else "✗"
                quality = "Excelente" if r2_score >= 0.85 else "Bueno" if r2_score >= 0.70 else "Mejorar"
                
                print(f"\n  {status} {field}:")
                print(f"    R²: {r2_percent:.2f}% ({quality})")
                print(f"    RMSE: {metric['test_rmse']:.2f}")
                print(f"    MAE: {metric['test_mae']:.2f}")
                print(f"    Muestras: {metric['samples']}")
        else:
            print("✗ No se pudo entrenar")
            return False
        
        trainer.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("="*60)
    print(" TEST DE PREDICCIONES ML ".center(60))
    print("="*60)
    
    # Verificar datos
    check_data()
    
    # Verificar modelos
    check_models()
    
    # Menú
    print("\n" + "="*60)
    print("Opciones:")
    print("  1. Probar predicción (requiere modelos entrenados)")
    print("  2. Entrenar modelos (requiere datos)")
    print("  3. Ambos (entrenar y luego predecir)")
    print("  0. Salir")
    
    choice = input("\nSeleccione una opción: ").strip()
    
    if choice == '0':
        return
    
    # Seleccionar sensor
    print("\nSensor:")
    for i, sensor in enumerate(Config.SENSOR_TYPES, 1):
        print(f"  {i}. {sensor.capitalize()}")
    
    sensor_choice = input("Seleccione sensor: ").strip()
    
    try:
        sensor_idx = int(sensor_choice) - 1
        if 0 <= sensor_idx < len(Config.SENSOR_TYPES):
            sensor_type = Config.SENSOR_TYPES[sensor_idx]
        else:
            print("Opción inválida")
            return
    except ValueError:
        print("Opción inválida")
        return
    
    # Ejecutar acción
    if choice == '1':
        test_prediction(sensor_type)
    elif choice == '2':
        test_training(sensor_type)
    elif choice == '3':
        if test_training(sensor_type):
            print("\n" + "="*60)
            input("Presione Enter para continuar con la predicción...")
            test_prediction(sensor_type)
    else:
        print("Opción inválida")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Prueba cancelada")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()