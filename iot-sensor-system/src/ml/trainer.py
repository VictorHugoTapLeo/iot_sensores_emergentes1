"""
ML Trainer - Entrenamiento de modelos de Machine Learning
"""
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
from pathlib import Path
from src.config.settings import Config
from src.database.mongodb_manager import MongoDBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SensorMLTrainer:
    """Entrenador de modelos ML para sensores IoT"""
    
    def __init__(self, sensor_type):
        """
        Inicializar entrenador
        
        Args:
            sensor_type: Tipo de sensor ('aire', 'sonido', 'soterrado')
        """
        self.sensor_type = sensor_type
        self.db_manager = MongoDBManager()
        self.models = {}
        self.scalers = {}
        self.metrics = {}
        
        # Campos a predecir según tipo de sensor
        self.target_fields = {
            'aire': ['object.co2', 'object.temperature', 'object.humidity', 'object.pressure'],
            'sonido': ['object.LAeq', 'object.LAI', 'object.LAImax'],
            'soterrado': ['object.distance']
        }
    
    def load_data(self, days=60):
        """
        Cargar datos de MongoDB para entrenamiento
        
        Args:
            days: Días de datos históricos a cargar (0 = todos los datos)
            
        Returns:
            DataFrame con los datos
        """
        if days == 0:
            logger.info(f"Cargando TODOS los datos de {self.sensor_type}...")
            # Obtener todos los datos disponibles
            raw_data = self.db_manager.get_latest_data(self.sensor_type, limit=10000)
        else:
            logger.info(f"Cargando datos de {self.sensor_type} ({days} días)...")
            raw_data = self.db_manager.get_data_for_ml_training(self.sensor_type, days)
        
        if not raw_data:
            logger.warning("No hay datos disponibles")
            return None
        
        # Convertir a DataFrame
        df = pd.DataFrame(raw_data)
        
        # Parsear timestamp
        df['timestamp'] = pd.to_datetime(df['time'])
        df = df.sort_values('timestamp')
        
        logger.info(f"✓ Datos cargados: {len(df)} registros")
        return df
    
    def prepare_features(self, df):
        """
        Preparar features para entrenamiento
        
        Args:
            df: DataFrame con datos crudos
            
        Returns:
            DataFrame con features preparados
        """
        # Extraer características temporales
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        
        # Crear features cíclicos para capturar patrones temporales
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Features de tendencia (índice temporal normalizado)
        df['time_index'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
        df['time_index'] = df['time_index'] / df['time_index'].max()
        
        return df
    
    def train_model_for_field(self, df, field):
        """
        Entrenar modelo para un campo específico
        
        Args:
            df: DataFrame con datos
            field: Campo a predecir
            
        Returns:
            Modelo entrenado, scaler y métricas
        """
        logger.info(f"Entrenando modelo para: {field}")
        
        # Verificar que el campo existe y tiene datos válidos
        if field not in df.columns:
            logger.warning(f"Campo {field} no encontrado en datos")
            return None, None, {}
        
        # Limpiar datos nulos
        df_clean = df.dropna(subset=[field])
        
        if len(df_clean) < 50:
            logger.warning(f"Datos insuficientes para {field}: {len(df_clean)} registros")
            return None, None, {}
        
        # Features
        feature_cols = ['hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'time_index']
        X = df_clean[feature_cols].values
        y = df_clean[field].values
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Escalar features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Entrenar modelo (Random Forest para mejor captura de patrones)
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Predicciones
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
        
        # Métricas
        metrics = {
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'samples': len(df_clean)
        }
        
        logger.info(f"""
        Métricas para {field}:
        - R² (test): {metrics['test_r2']:.4f}
        - RMSE (test): {metrics['test_rmse']:.4f}
        - MAE (test): {metrics['test_mae']:.4f}
        - Samples: {metrics['samples']}
        """)
        
        return model, scaler, metrics
    
    def train_all(self, days=60):
        """
        Entrenar modelos para todos los campos del sensor
        
        Args:
            days: Días de datos históricos
            
        Returns:
            Diccionario con métricas generales
        """
        logger.info(f"\n{'='*60}")
        logger.info(f" ENTRENAMIENTO ML - {self.sensor_type.upper()} ".center(60))
        logger.info(f"{'='*60}\n")
        
        # Cargar datos
        df = self.load_data(days)
        if df is None or len(df) == 0:
            logger.error("No hay datos suficientes para entrenar")
            return None
        
        # Preparar features
        df = self.prepare_features(df)
        
        # Entrenar modelo para cada campo
        fields = self.target_fields.get(self.sensor_type, [])
        
        for field in fields:
            model, scaler, metrics = self.train_model_for_field(df, field)
            
            if model is not None:
                self.models[field] = model
                self.scalers[field] = scaler
                self.metrics[field] = metrics
        
        # Guardar modelos
        if self.models:
            self.save_models()
            logger.info(f"\n✓ Entrenamiento completado: {len(self.models)} modelos")
            return self.metrics
        else:
            logger.warning("No se entrenó ningún modelo")
            return None
    
    def save_models(self):
        """Guardar modelos entrenados"""
        models_path = Config.ML_MODELS_PATH / self.sensor_type
        models_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for field, model in self.models.items():
            # Limpiar nombre del campo para archivo
            field_name = field.replace('object.', '').replace('.', '_')
            
            model_file = models_path / f"{field_name}_model_{timestamp}.joblib"
            scaler_file = models_path / f"{field_name}_scaler_{timestamp}.joblib"
            
            joblib.dump(model, model_file)
            joblib.dump(self.scalers[field], scaler_file)
            
            logger.info(f"✓ Modelo guardado: {model_file.name}")
        
        # Guardar métricas
        metrics_file = models_path / f"metrics_{timestamp}.joblib"
        joblib.dump(self.metrics, metrics_file)
        logger.info(f"✓ Métricas guardadas: {metrics_file.name}")
    
    def close(self):
        """Cerrar conexiones"""
        self.db_manager.close()


def main():
    """Función principal para entrenar modelos"""
    import sys
    
    print("="*60)
    print(" ENTRENAMIENTO DE MODELOS ML ".center(60))
    print("="*60)
    
    print("\nSensores disponibles:")
    for i, sensor in enumerate(Config.SENSOR_TYPES, 1):
        print(f"  {i}. {sensor.capitalize()}")
    print(f"  {len(Config.SENSOR_TYPES) + 1}. Entrenar TODOS")
    
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
    
    days = int(input("\n¿Cuántos días de datos usar? (recomendado: 60): ") or 60)
    
    # Entrenar modelos
    for sensor in sensors:
        trainer = SensorMLTrainer(sensor)
        try:
            trainer.train_all(days)
        finally:
            trainer.close()
    
    print("\n" + "="*60)
    print(" ENTRENAMIENTO COMPLETADO ".center(60))
    print("="*60)


if __name__ == "__main__":
    main()