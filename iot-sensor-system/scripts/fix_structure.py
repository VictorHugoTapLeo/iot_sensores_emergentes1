#!/usr/bin/env python3
"""
Script para corregir la estructura del proyecto
Crea archivos __init__.py faltantes y verifica la estructura
"""
from pathlib import Path
import sys

def create_init_files():
    """Crear archivos __init__.py en todas las carpetas Python"""
    
    init_paths = [
        'src/__init__.py',
        'src/config/__init__.py',
        'src/data_ingestion/__init__.py',
        'src/database/__init__.py',
        'src/ml/__init__.py',
        'src/api/__init__.py',
        'src/api/routes/__init__.py',
        'src/api/middleware/__init__.py',
        'src/utils/__init__.py',
        'tests/__init__.py'
    ]
    
    print("Creando archivos __init__.py...")
    for path_str in init_paths:
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if not path.exists():
            path.touch()
            print(f"✓ Creado: {path}")
        else:
            print(f"  Ya existe: {path}")

def check_critical_files():
    """Verificar archivos críticos del proyecto"""
    
    critical_files = {
        'docker-compose.yml': 'Configuración Docker',
        'requirements.txt': 'Dependencias Python',
        '.env': 'Variables de entorno',
        'src/config/settings.py': 'Configuración',
        'src/data_ingestion/csv_producer.py': 'Productor Kafka',
        'src/data_ingestion/kafka_consumer.py': 'Consumidor Kafka',
        'src/database/mongodb_manager.py': 'Gestor MongoDB',
        'src/database/postgres_manager.py': 'Gestor PostgreSQL',
        'src/ml/trainer.py': 'Entrenador ML',
        'src/ml/predictor.py': 'Predictor ML',
        'src/api/app.py': 'API Flask',
        'src/api/routes/auth.py': 'Rutas Auth',
        'src/api/routes/sensors.py': 'Rutas Sensores',
        'src/api/routes/predictions.py': 'Rutas Predicciones',
        'src/api/middleware/auth_middleware.py': 'Middleware JWT',
        'frontend/index.html': 'Frontend HTML',
        'frontend/css/style.css': 'Estilos CSS',
        'frontend/js/app.js': 'JavaScript App'
    }
    
    print("\nVerificando archivos críticos...")
    missing_files = []
    
    for file_path, description in critical_files.items():
        path = Path(file_path)
        if path.exists():
            print(f"✓ {description}: {file_path}")
        else:
            print(f"✗ FALTA {description}: {file_path}")
            missing_files.append((file_path, description))
    
    return missing_files

def fix_routes_init():
    """Corregir src/api/routes/__init__.py"""
    
    routes_init = Path('src/api/routes/__init__.py')
    
    # Contenido correcto (vacío o mínimo)
    content = '"""\\nRoutes Package - Rutas de la API\\n"""\\n'
    
    if routes_init.exists():
        routes_init.write_text(content, encoding='utf-8')
        print(f"✓ Corregido: {routes_init}")
    else:
        routes_init.parent.mkdir(parents=True, exist_ok=True)
        routes_init.write_text(content, encoding='utf-8')
        print(f"✓ Creado: {routes_init}")

def create_directories():
    """Crear directorios necesarios"""
    
    directories = [
        'data',
        'src/ml/models',
        'logs',
        'frontend/css',
        'frontend/js',
        'frontend/assets',
        'scripts',
        'tests'
    ]
    
    print("\nCreando directorios...")
    for dir_path in directories:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Creado: {dir_path}")
        else:
            print(f"  Ya existe: {dir_path}")

def check_sensors_file():
    """Verificar y corregir archivo sensors.py"""
    
    sensors_path = Path('src/api/routes/sensors.py')
    old_path = Path('src/api/routes/sensors_routes.py')
    
    print("\nVerificando archivo sensors.py...")
    
    if sensors_path.exists():
        print(f"✓ Existe: {sensors_path}")
        return True
    elif old_path.exists():
        print(f"⚠ Encontrado: {old_path}")
        print(f"  Renombrando a: {sensors_path}")
        old_path.rename(sensors_path)
        print("✓ Renombrado correctamente")
        return True
    else:
        print(f"✗ FALTA: {sensors_path}")
        print("  Este archivo debe ser copiado de los artifacts generados")
        return False

def main():
    """Función principal"""
    
    print("="*60)
    print(" CORRECCIÓN DE ESTRUCTURA DEL PROYECTO ".center(60))
    print("="*60)
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)
    
    # Crear directorios
    create_directories()
    
    # Crear archivos __init__.py
    create_init_files()
    
    # Corregir routes __init__
    fix_routes_init()
    
    # Verificar archivo sensors
    sensors_ok = check_sensors_file()
    
    # Verificar archivos críticos
    missing_files = check_critical_files()
    
    # Resumen
    print("\n" + "="*60)
    print(" RESUMEN ".center(60))
    print("="*60)
    
    if missing_files:
        print("\n⚠ ARCHIVOS FALTANTES:")
        for file_path, description in missing_files:
            print(f"  - {description}: {file_path}")
        print("\nCopie estos archivos de los artifacts generados")
    else:
        print("\n✓ Todos los archivos críticos están presentes")
    
    if sensors_ok:
        print("✓ Archivo sensors.py correcto")
    else:
        print("✗ Falta archivo sensors.py")
    
    print("\n" + "="*60)
    
    if missing_files and not sensors_ok:
        print("\n⚠ Hay archivos faltantes. Copie los archivos necesarios.")
        sys.exit(1)
    elif missing_files or not sensors_ok:
        print("\n⚠ Algunos archivos faltan. Verifique arriba.")
        sys.exit(1)
    else:
        print("\n✅ Estructura del proyecto correcta!")
        print("\nPuede continuar con:")
        print("  python -m src.api.app")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)