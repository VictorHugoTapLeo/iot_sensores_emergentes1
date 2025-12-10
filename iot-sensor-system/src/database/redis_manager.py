"""
Redis Manager - Gestor de cache y sesiones
"""
import logging
import json
import redis
from src.config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisManager:
    """Gestor de operaciones con Redis"""
    
    def __init__(self):
        """Inicializar conexión a Redis"""
        try:
            self.client = redis.Redis(**Config.REDIS_CONFIG, decode_responses=True)
            self.client.ping()
            logger.info("✓ Conectado a Redis")
        except Exception as e:
            logger.error(f"✗ Error conectando a Redis: {e}")
            self.client = None
    
    def set(self, key, value, expire=None):
        """
        Guardar valor en cache
        
        Args:
            key: Clave
            value: Valor (se convertirá a JSON si es dict/list)
            expire: Tiempo de expiración en segundos
        """
        if not self.client:
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if expire:
                self.client.setex(key, expire, value)
            else:
                self.client.set(key, value)
            
            return True
        except Exception as e:
            logger.error(f"Error guardando en Redis: {e}")
            return False
    
    def get(self, key):
        """
        Obtener valor del cache
        
        Args:
            key: Clave
            
        Returns:
            Valor o None si no existe
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return None
        except Exception as e:
            logger.error(f"Error obteniendo de Redis: {e}")
            return None
    
    def delete(self, key):
        """Eliminar clave"""
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error eliminando de Redis: {e}")
            return False
    
    def exists(self, key):
        """Verificar si existe una clave"""
        if not self.client:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error verificando existencia: {e}")
            return False
    
    def increment(self, key, amount=1):
        """Incrementar valor numérico"""
        if not self.client:
            return None
        
        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementando: {e}")
            return None
    
    def close(self):
        """Cerrar conexión"""
        if self.client:
            self.client.close()
            logger.info("✓ Conexión Redis cerrada")