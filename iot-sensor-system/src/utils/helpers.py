"""
Helpers - Funciones auxiliares comunes
"""
from datetime import datetime, timedelta
import json
from typing import Any, Dict, List

def parse_datetime(date_string):
    """
    Parsear string a datetime
    
    Args:
        date_string: String con fecha ISO
        
    Returns:
        datetime object
    """
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except Exception:
        return None

def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Formatear datetime a string
    
    Args:
        dt: datetime object
        format_str: Formato de salida
        
    Returns:
        String formateado
    """
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    
    if dt:
        return dt.strftime(format_str)
    return None

def get_date_range(days_back=30):
    """
    Obtener rango de fechas
    
    Args:
        days_back: Días hacia atrás
        
    Returns:
        Tuple (start_date, end_date)
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date

def clean_mongo_document(doc):
    """
    Limpiar documento de MongoDB para JSON
    
    Args:
        doc: Documento de MongoDB
        
    Returns:
        Documento limpio
    """
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [clean_mongo_document(item) for item in doc]
    
    if isinstance(doc, dict):
        cleaned = {}
        for key, value in doc.items():
            if key == '_id':
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = clean_mongo_document(value)
            elif isinstance(value, list):
                cleaned[key] = [clean_mongo_document(item) for item in value]
            else:
                cleaned[key] = value
        return cleaned
    
    return doc

def paginate(items: List[Any], page: int = 1, per_page: int = 50) -> Dict:
    """
    Paginar lista de items
    
    Args:
        items: Lista de items
        page: Número de página (empieza en 1)
        per_page: Items por página
        
    Returns:
        Dict con items paginados y metadata
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }

def safe_float(value, default=0.0):
    """
    Convertir valor a float de forma segura
    
    Args:
        value: Valor a convertir
        default: Valor por defecto
        
    Returns:
        Float o default
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def safe_int(value, default=0):
    """
    Convertir valor a int de forma segura
    
    Args:
        value: Valor a convertir
        default: Valor por defecto
        
    Returns:
        Int o default
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def validate_sensor_type(sensor_type):
    """
    Validar tipo de sensor
    
    Args:
        sensor_type: Tipo a validar
        
    Returns:
        bool
    """
    from src.config.settings import Config
    return sensor_type in Config.SENSOR_TYPES

def calculate_statistics(values):
    """
    Calcular estadísticas básicas
    
    Args:
        values: Lista de valores numéricos
        
    Returns:
        Dict con estadísticas
    """
    import numpy as np
    
    if not values:
        return {
            'mean': 0,
            'median': 0,
            'std': 0,
            'min': 0,
            'max': 0,
            'count': 0
        }
    
    values = [v for v in values if v is not None]
    
    return {
        'mean': float(np.mean(values)),
        'median': float(np.median(values)),
        'std': float(np.std(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'count': len(values)
    }