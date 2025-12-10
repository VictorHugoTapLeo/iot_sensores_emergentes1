"""
ML Predictor - Genera predicciones usando modelos entrenados
"""
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
from pathlib import Path
from src.config.settings import Config
from src.database.mongodb_manager import MongoDBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SensorMLPredictor:
    """Predictor de valores futuros para sensores IoT"""
    
    def __init__(self, sensor_type):
        """
        Inicializar predictor
        
        Args:
            sensor_type: Tipo de sensor ('aire', 'sonido', 'soterrado')
        """
        self.sensor_type = sensor_type
        self.db_manager = MongoDBManager()
        self.models = {}
        self.scalers = {}
        self.load_models()
    
    def load_models(self):
        """Cargar modelos entrenados más recientes"""
        models_path = Config.ML_MODELS_PATH / self.sensor_type
        
        if not models_path.exists():
            logger.warning(f"No hay modelos entrenados para {self.sensor_type}")
            return
        
        # Buscar archivos de modelos
        model_files = sorted(models_path.glob("*_model_*.joblib"), reverse=True)
        
        if not model_files:
            logger.warning(f"No se encontraron modelos para {self.sensor_type}")
            return
        
        # Obtener timestamp del modelo más reciente
        latest_timestamp = model_files[0].stem.split('_')[-2] + '_' + model_files[0].stem.split('_')[-1]
        
        # Cargar todos los modelos y scalers de ese timestamp
        for model_file in models_path.glob(f"*_model_{latest_timestamp}.joblib"):
            field_name = model_file.stem.replace(f'_model_{latest_timestamp}', '')
            scaler_file = models_path / f"{field_name}_scaler_{latest_timestamp}.joblib"
            
            if scaler_file.exists():
                self.models[field_name] = joblib.load(model_file)
                self.scalers[field_name] = joblib.load(scaler_file)
                logger.info(f"✓ Modelo cargado: {field_name}")
        
        logger.info(f"Modelos cargados para {self.sensor_type}: {len(self.models)}")
    
    def create_future_features(self, start_date, periods, freq='H'):
        """
        Crear features para fechas futuras
        
        Args:
            start_date: Fecha de inicio
            periods: Número de períodos a predecir
            freq: Frecuencia ('H' = hourly, 'D' = daily)
            
        Returns:
            DataFrame con features
        """
        # Crear rango de fechas futuras
        future_dates = pd.date_range(start=start_date, periods=periods, freq=freq)
        
        df = pd.DataFrame({'timestamp': future_dates})
        
        # Características temporales
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        
        # Features cíclicos
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Time index (continuar desde el último dato)
        df['time_index'] = np.linspace(1.0, 1.1, len(df))
        
        return df
    
    def predict(self, days=7, freq='H'):
        """
        Generar predicciones
        
        Args:
            days: Días a predecir
            freq: Frecuencia de predicción ('H' = hourly, 'D' = daily)
            
        Returns:
            Diccionario con predicciones por campo
        """
        if not self.models:
            logger.warning("No hay modelos cargados")
            return None
        
        logger.info(f"Generando predicciones para {days} días ({freq})...")
        
        # Obtener última fecha de datos
        latest_data = self.db_manager.get_latest_data(self.sensor_type, limit=1)
        
        if not latest_data:
            logger.warning("No hay datos históricos")
            start_date = datetime.utcnow()
        else:
            start_date = datetime.fromisoformat(latest_data[0]['time'].replace('Z', '+00:00'))
        
        # Calcular períodos según frecuencia
        periods = days * 24 if freq == 'H' else days
        
        # Crear features futuras
        future_df = self.create_future_features(start_date, periods, freq)
        
        # Features para predicción
        feature_cols = ['hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'time_index']
        X_future = future_df[feature_cols].values
        
        # Generar predicciones para cada campo
        predictions = {
            'timestamps': future_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            'predictions': {}
        }
        
        for field_name, model in self.models.items():
            scaler = self.scalers[field_name]
            
            # Escalar y predecir
            X_scaled = scaler.transform(X_future)
            y_pred = model.predict(X_scaled)
            
            # Convertir nombre de campo
            full_field = f"object.{field_name.replace('_', '.')}"
            
            predictions['predictions'][full_field] = y_pred.tolist()
            
            logger.info(f"✓ Predicciones generadas para: {full_field}")
        
        # Agregar metadatos
        predictions['metadata'] = {
            'sensor_type': self.sensor_type,
            'generated_at': datetime.utcnow().isoformat(),
            'prediction_days': days,
            'frequency': freq,
            'total_predictions': len(predictions['timestamps'])
        }
        
        return predictions
    
    def predict_multiple_periods(self):
        """
        Generar predicciones para 7 y 30 días
        
        Returns:
            Diccionario con predicciones cortas y largas
        """
        logger.info(f"\n{'='*60}")
        logger.info(f" PREDICCIONES ML - {self.sensor_type.upper()} ".center(60))
        logger.info(f"{'='*60}\n")
        
        predictions = {}
        
        # Predicción a 7 días (cada hora)
        logger.info("Predicción a 7 días...")
        pred_7d = self.predict(days=7, freq='H')
        if pred_7d:
            predictions['7_days'] = pred_7d
        
        # Predicción a 30 días (diaria)
        logger.info("\nPredicción a 30 días...")
        pred_30d = self.predict(days=30, freq='D')
        if pred_30d:
            predictions['30_days'] = pred_30d
        
        # Guardar predicciones en MongoDB
        if predictions:
            self.db_manager.save_prediction(self.sensor_type, predictions)
            logger.info("\n✓ Predicciones guardadas en MongoDB")
        
        return predictions
    
    def get_prediction_summary(self, predictions):
        """
        Obtener resumen estadístico de predicciones
        
        Args:
            predictions: Diccionario con predicciones
            
        Returns:
            Diccionario con estadísticas
        """
        summary = {}
        
        for period in ['7_days', '30_days']:
            if period not in predictions:
                continue
            
            period_data = predictions[period]['predictions']
            summary[period] = {}
            
            for field, values in period_data.items():
                summary[period][field] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'median': np.median(values)
                }
        
        return summary
    
    def close(self):
        """Cerrar conexiones"""
        self.db_manager.close()


def main():
    """Función principal para generar predicciones"""
    import sys
    import json
    
    print("="*60)
    print(" GENERACIÓN DE PREDICCIONES ML ".center(60))
    print("="*60)
    
    print("\nSensores disponibles:")
    for i, sensor in enumerate(Config.SENSOR_TYPES, 1):
        print(f"  {i}. {sensor.capitalize()}")
    print(f"  {len(Config.SENSOR_TYPES) + 1}. Predecir TODOS")
    
    choice = input("\nSeleccione una opción: ").strip()
    
    try:
        choice_num = int(choice)
        
        if choice_num == len(Config.SENSOR_TYPES) + 1:
            sensors = Config.SENSOR_TYPES
        elif 1 <= choice_num <= len(Config.SENSOR_TYPES):
            sensors = [Config.SENSOR_TYPES[choice_num - 1]]
        else:
            print("Opción inválida")
            sys.exit(1)
    except ValueError:
        print("Opción inválida")
        sys.exit(1)
    
    # Generar predicciones
    for sensor in sensors:
        predictor = SensorMLPredictor(sensor)
        try:
            predictions = predictor.predict_multiple_periods()
            
            if predictions:
                summary = predictor.get_prediction_summary(predictions)
                print(f"\nResumen de predicciones para {sensor}:")
                print(json.dumps(summary, indent=2))
        finally:
            predictor.close()
    
    print("\n" + "="*60)
    print(" PREDICCIONES COMPLETADAS ".center(60))
    print("="*60)


if __name__ == "__main__":
    main()