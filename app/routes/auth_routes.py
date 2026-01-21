"""
Rutas de autenticación y gestión de usuarios
"""

from flask import Blueprint, jsonify, request, session
from app.interface.users import UserInterface
from app.interface.interfaces import AuditLogInterface
from app.utils.logger import get_logger
from app.utils.config import db
from functools import wraps

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def login_required(f):
    """Decorator para requerir login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator para requerir rol admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login de usuario"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username y password requeridos'}), 400
        
        user = UserInterface.authenticate(username, password)
        if not user:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        # Crear sesión
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['person_id'] = user.person_id
        
        # Registrar en auditoría
        AuditLogInterface.create({
            'action': 'login',
            'entity_type': 'user',
            'entity_id': user.id,
            'performed_by': user.username,
            'ip_address': request.remote_addr
        })
        
        return jsonify({
            'message': 'Login exitoso',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en login: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout de usuario"""
    try:
        username = session.get('username')
        
        # Registrar en auditoría
        AuditLogInterface.create({
            'action': 'logout',
            'entity_type': 'user',
            'performed_by': username,
            'ip_address': request.remote_addr
        })
        
        session.clear()
        return jsonify({'message': 'Logout exitoso'}), 200
        
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Obtener usuario actual"""
    try:
        user_id = session.get('user_id')
        user = UserInterface.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Error al obtener usuario actual: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario actual"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Contraseñas requeridas'}), 400
        
        UserInterface.change_password(user_id, old_password, new_password)
        
        # Registrar en auditoría
        AuditLogInterface.create({
            'action': 'change_password',
            'entity_type': 'user',
            'entity_id': user_id,
            'performed_by': session.get('username'),
            'ip_address': request.remote_addr
        })
        
        return jsonify({'message': 'Contraseña actualizada'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error al cambiar contraseña: {e}")
        return jsonify({'error': str(e)}), 500


# ===== RUTAS DE GESTIÓN DE USUARIOS (SOLO ADMIN) =====

@auth_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Obtener todos los usuarios (solo admin)"""
    try:
        users = UserInterface.get_all_users()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Crear nuevo usuario (solo admin)"""
    try:
        data = request.get_json()
        data['created_by'] = session.get('username')
        
        user = UserInterface.create_user(data)
        
        # Registrar en auditoría
        AuditLogInterface.create({
            'action': 'create',
            'entity_type': 'user',
            'entity_id': user.id,
            'new_value': user.to_dict(),
            'performed_by': session.get('username'),
            'ip_address': request.remote_addr
        })
        
        return jsonify({
            'message': 'Usuario creado',
            'user': user.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error al crear usuario: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Actualizar usuario (solo admin)"""
    try:
        data = request.get_json()
        
        old_user = UserInterface.get_user_by_id(user_id)
        old_value = old_user.to_dict() if old_user else None
        
        user = UserInterface.update_user(user_id, data)
        
        # Registrar en auditoría
        AuditLogInterface.create({
            'action': 'update',
            'entity_type': 'user',
            'entity_id': user_id,
            'old_value': old_value,
            'new_value': user.to_dict(),
            'performed_by': session.get('username'),
            'ip_address': request.remote_addr
        })
        
        return jsonify({
            'message': 'Usuario actualizado',
            'user': user.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Eliminar usuario (solo admin)"""
    try:
        # No permitir eliminar el propio usuario
        if user_id == session.get('user_id'):
            return jsonify({'error': 'No puedes eliminar tu propio usuario'}), 400
        
        user = UserInterface.get_user_by_id(user_id)
        old_value = user.to_dict() if user else None
        
        UserInterface.delete_user(user_id)
        
        # Registrar en auditoría
        AuditLogInterface.create({
            'action': 'delete',
            'entity_type': 'user',
            'entity_id': user_id,
            'old_value': old_value,
            'performed_by': session.get('username'),
            'ip_address': request.remote_addr
        })
        
        return jsonify({'message': 'Usuario eliminado'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """Resetear contraseña de un usuario (solo admin)"""
    try:
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'error': 'Nueva contraseña requerida'}), 400
        
        user = UserInterface.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Actualizar contraseña
        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        # Registrar en auditoría
        AuditLogInterface.create({
            'action': 'reset_password',
            'entity_type': 'user',
            'entity_id': user_id,
            'performed_by': session.get('username'),
            'ip_address': request.remote_addr,
            'notes': f'Contraseña reseteada para {user.username}'
        })
        
        return jsonify({
            'message': 'Contraseña actualizada correctamente',
            'username': user.username
        }), 200
        
    except Exception as e:
        logger.error(f"Error al resetear contraseña: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/users/by-role/<string:role>', methods=['GET'])
@admin_required
def get_users_by_role(role):
    """Obtener usuarios por rol (solo admin)"""
    try:
        users = UserInterface.get_users_by_role(role)
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener usuarios por rol: {e}")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/users/<int:user_id>/permissions', methods=['PATCH'])
@admin_required
def update_user_permissions(user_id):
    """Actualizar permisos de acceso a páginas de un usuario"""
    try:
        from app.models.models import User
        
        data = request.get_json()
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Guardar valores antiguos para auditoría
        old_permissions = {
            'can_access_operator_view': user.can_access_operator_view,
            'can_access_device_analysis': user.can_access_device_analysis
        }
        
        # Actualizar permisos enviados
        if 'can_access_operator_view' in data:
            user.can_access_operator_view = bool(data['can_access_operator_view'])
        
        if 'can_access_device_analysis' in data:
            user.can_access_device_analysis = bool(data['can_access_device_analysis'])
        
        db.session.commit()
        
        # Registrar en auditoría
        new_permissions = {
            'can_access_operator_view': user.can_access_operator_view,
            'can_access_device_analysis': user.can_access_device_analysis
        }
        
        AuditLogInterface.create({
            'action': 'update_permissions',
            'entity_type': 'user',
            'entity_id': user_id,
            'old_value': old_permissions,
            'new_value': new_permissions,
            'performed_by': session.get('username'),
            'ip_address': request.remote_addr,
            'notes': f'Permisos actualizados para {user.username}'
        })
        
        logger.info(f"✅ Permisos actualizados para usuario {user.username}")
        
        return jsonify({
            'message': 'Permisos actualizados correctamente',
            'permissions': {
                'can_access_operator_view': user.can_access_operator_view,
                'can_access_device_analysis': user.can_access_device_analysis
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error al actualizar permisos: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
