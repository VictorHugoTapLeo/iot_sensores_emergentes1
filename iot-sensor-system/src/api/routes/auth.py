"""
Auth Routes - Rutas de autenticación
"""
import logging
from flask import Blueprint, request, jsonify
from src.database.postgres_manager import PostgresManager
from src.api.middleware.auth_middleware import generate_token, token_required

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)
db = PostgresManager()

@bp.route('/login', methods=['POST'])
def login():
    """
    Login de usuario
    
    Body:
        {
            "username": "string",
            "password": "string"
        }
    """
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Usuario y contraseña requeridos'}), 400
        
        # Autenticar usuario
        user = db.authenticate_user(username, password)
        
        if not user:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        # Generar token
        token = generate_token(user)
        
        # Log de acción
        ip_address = request.remote_addr
        db.log_action(user['id'], 'LOGIN', details='Login exitoso', ip_address=ip_address)
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role'],
                'email': user['email']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error en login: {e}")
        return jsonify({'error': 'Error en el servidor'}), 500

@bp.route('/verify', methods=['GET'])
@token_required
def verify():
    """
    Verificar token JWT
    """
    return jsonify({
        'valid': True,
        'user': request.user
    }), 200

@bp.route('/profile', methods=['GET'])
@token_required
def profile():
    """
    Obtener perfil del usuario
    """
    try:
        user = db.get_user_by_username(request.user['username'])
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'email': user['email'],
            'role': user['role'],
            'last_login': user['last_login'].isoformat() if user['last_login'] else None,
            'created_at': user['created_at'].isoformat() if user['created_at'] else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo perfil: {e}")
        return jsonify({'error': 'Error en el servidor'}), 500

@bp.route('/users', methods=['GET'])
@token_required
def get_users():
    """
    Obtener lista de usuarios (solo admin)
    """
    # Solo admins pueden ver lista de usuarios
    if 'admin' not in request.user['role']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    # TODO: Implementar obtención de usuarios
    return jsonify({'users': []}), 200