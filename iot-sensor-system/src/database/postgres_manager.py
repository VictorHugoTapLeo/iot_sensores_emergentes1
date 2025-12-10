"""
PostgreSQL Manager - Gestor para usuarios, autenticación y logs
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import bcrypt
from src.config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgresManager:
    """Gestor de PostgreSQL para usuarios y logs"""
    
    def __init__(self):
        """Inicializar conexión"""
        self.conn = None
        self.connect()
        self.init_tables()
    
    def connect(self):
        """Conectar a PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**Config.POSTGRES_CONFIG)
            logger.info("✓ Conectado a PostgreSQL")
        except Exception as e:
            logger.error(f"✗ Error conectando a PostgreSQL: {e}")
            raise
    
    def init_tables(self):
        """Crear tablas si no existen"""
        try:
            with self.conn.cursor() as cur:
                # Tabla de usuarios
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # Tabla de logs de acciones
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS action_logs (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        action VARCHAR(50) NOT NULL,
                        resource VARCHAR(100),
                        details TEXT,
                        ip_address VARCHAR(50),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla de logs de sistema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id SERIAL PRIMARY KEY,
                        level VARCHAR(20) NOT NULL,
                        message TEXT NOT NULL,
                        module VARCHAR(100),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.conn.commit()
                logger.info("✓ Tablas inicializadas")
                
                # Crear usuarios por defecto si no existen
                self.create_default_users()
                
        except Exception as e:
            logger.error(f"Error inicializando tablas: {e}")
            self.conn.rollback()
    
    def create_default_users(self):
        """Crear usuarios por defecto del sistema"""
        default_users = [
            {
                'username': 'alcalde',
                'password': 'alcalde123',
                'full_name': 'Alcalde GAMC',
                'email': 'alcalde@gamc.gob.bo',
                'role': Config.ROLES['ALCALDE']
            },
            {
                'username': 'director',
                'password': 'director123',
                'full_name': 'Director DGEyCI',
                'email': 'director@gamc.gob.bo',
                'role': Config.ROLES['DIRECTOR']
            },
            {
                'username': 'admin',
                'password': 'admin123',
                'full_name': 'Administrador Sistema',
                'email': 'admin@gamc.gob.bo',
                'role': Config.ROLES['ADMIN']
            },
            {
                'username': 'usuario',
                'password': 'usuario123',
                'full_name': 'Usuario Operativo',
                'email': 'usuario@gamc.gob.bo',
                'role': Config.ROLES['USER']
            }
        ]
        
        for user_data in default_users:
            if not self.get_user_by_username(user_data['username']):
                self.create_user(**user_data)
                logger.info(f"Usuario creado: {user_data['username']}")
    
    def hash_password(self, password):
        """Hash de contraseña con bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, password_hash):
        """Verificar contraseña"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_user(self, username, password, full_name, email, role):
        """Crear nuevo usuario"""
        try:
            password_hash = self.hash_password(password)
            
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, role)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (username, password_hash, full_name, email, role))
                
                user_id = cur.fetchone()[0]
                self.conn.commit()
                return user_id
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            self.conn.rollback()
            return None
    
    def get_user_by_username(self, username):
        """Obtener usuario por username"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM users WHERE username = %s AND is_active = TRUE
                """, (username,))
                return cur.fetchone()
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None
    
    def authenticate_user(self, username, password):
        """Autenticar usuario"""
        user = self.get_user_by_username(username)
        
        if user and self.verify_password(password, user['password_hash']):
            # Actualizar último login
            self.update_last_login(user['id'])
            return user
        return None
    
    def update_last_login(self, user_id):
        """Actualizar timestamp de último login"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (user_id,))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error actualizando login: {e}")
            self.conn.rollback()
    
    def log_action(self, user_id, action, resource=None, details=None, ip_address=None):
        """Registrar acción de usuario"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO action_logs (user_id, action, resource, details, ip_address)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, action, resource, details, ip_address))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error registrando acción: {e}")
            self.conn.rollback()
    
    def log_system(self, level, message, module=None):
        """Registrar log de sistema"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO system_logs (level, message, module)
                    VALUES (%s, %s, %s)
                """, (level, message, module))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error registrando log: {e}")
            self.conn.rollback()
    
    def get_recent_logs(self, limit=100, log_type='action'):
        """Obtener logs recientes"""
        try:
            table = 'action_logs' if log_type == 'action' else 'system_logs'
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if log_type == 'action':
                    cur.execute(f"""
                        SELECT al.*, u.username, u.full_name
                        FROM {table} al
                        JOIN users u ON al.user_id = u.id
                        ORDER BY al.timestamp DESC
                        LIMIT %s
                    """, (limit,))
                else:
                    cur.execute(f"""
                        SELECT * FROM {table}
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (limit,))
                
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error obteniendo logs: {e}")
            return []
    
    def close(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()
            logger.info("✓ Conexión PostgreSQL cerrada")