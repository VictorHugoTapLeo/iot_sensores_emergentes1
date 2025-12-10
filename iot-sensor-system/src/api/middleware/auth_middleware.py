"""
Authentication Middleware - JWT Token Validation
"""
import jwt
import logging
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from src.config.settings import Config

logger = logging.getLogger(__name__)

def generate_token(user_data):
    """
    Generar token JWT
    
    Args:
        user_data: Datos del usuario
        
    Returns:
        Token JWT
    """
    payload = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'role': user_data['role'],
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token

def decode_token(token):
    """
    Decodificar token JWT
    
    Args:
        token: Token JWT
        
    Returns:
        Payload decodificado o None si es inválido
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Token inválido")
        return None

def token_required(f):
    """
    Decorador para proteger rutas con JWT
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Obtener token del header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Formato de token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        # Decodificar token
        payload = decode_token(token)
        
        if not payload:
            return jsonify({'error': 'Token inválido o expirado'}), 401
        
        # Agregar datos del usuario al request
        request.user = payload
        
        return f(*args, **kwargs)
    
    return decorated

def role_required(allowed_roles):
    """
    Decorador para verificar roles específicos
    
    Args:
        allowed_roles: Lista de roles permitidos
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'user'):
                return jsonify({'error': 'Usuario no autenticado'}), 401
            
            user_role = request.user.get('role')
            
            if user_role not in allowed_roles:
                return jsonify({'error': 'Permisos insuficientes'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator