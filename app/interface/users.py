"""
Interface para gestionar usuarios del sistema
"""

from typing import List, Optional, Dict, Any
from app.models.models import User
from app.utils.config import db
from app.utils.logger import get_logger
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

logger = get_logger(__name__)


class UserInterface:
    """Interfaz para operaciones CRUD de usuarios"""
    
    @staticmethod
    def get_all_users() -> List[User]:
        """Obtener todos los usuarios"""
        try:
            return User.query.all()
        except Exception as e:
            logger.error(f"Error al obtener usuarios: {e}")
            raise
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Obtener usuario por ID"""
        try:
            return User.query.get(user_id)
        except Exception as e:
            logger.error(f"Error al obtener usuario {user_id}: {e}")
            raise
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Obtener usuario por username"""
        try:
            return User.query.filter_by(username=username).first()
        except Exception as e:
            logger.error(f"Error al obtener usuario {username}: {e}")
            raise
    
    @staticmethod
    def create_user(data: Dict[str, Any]) -> User:
        """Crear nuevo usuario"""
        try:
            # Verificar si el username ya existe
            existing = UserInterface.get_user_by_username(data['username'])
            if existing:
                raise ValueError(f"El usuario {data['username']} ya existe")
            
            # Hash de la contraseña
            password_hash = generate_password_hash(data['password'])
            
            user = User(
                username=data['username'],
                password_hash=password_hash,
                full_name=data.get('full_name'),
                email=data.get('email'),
                role=data.get('role', 'operator'),
                person_id=data.get('person_id'),
                is_active=data.get('is_active', True),
                created_by=data.get('created_by', 'system')
            )
            
            db.session.add(user)
            db.session.commit()
            logger.info(f"Usuario creado: {user.username} (ID: {user.id})")
            return user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear usuario: {e}")
            raise
    
    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> User:
        """Actualizar usuario existente"""
        try:
            user = UserInterface.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"Usuario {user_id} no encontrado")
            
            # Actualizar campos
            if 'full_name' in data:
                user.full_name = data['full_name']
            if 'email' in data:
                user.email = data['email']
            if 'role' in data:
                user.role = data['role']
            if 'person_id' in data:
                user.person_id = data['person_id']
            if 'is_active' in data:
                user.is_active = data['is_active']
            if 'password' in data and data['password']:
                user.password_hash = generate_password_hash(data['password'])
            
            db.session.commit()
            logger.info(f"Usuario actualizado: {user.username} (ID: {user.id})")
            return user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar usuario {user_id}: {e}")
            raise
    
    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Eliminar usuario"""
        try:
            user = UserInterface.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"Usuario {user_id} no encontrado")
            
            username = user.username
            db.session.delete(user)
            db.session.commit()
            logger.info(f"Usuario eliminado: {username} (ID: {user_id})")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al eliminar usuario {user_id}: {e}")
            raise
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        """Autenticar usuario"""
        try:
            user = UserInterface.get_user_by_username(username)
            if not user:
                logger.warning(f"Intento de login con usuario inexistente: {username}")
                return None
            
            if not user.is_active:
                logger.warning(f"Intento de login con usuario inactivo: {username}")
                return None
            
            if not check_password_hash(user.password_hash, password):
                logger.warning(f"Contraseña incorrecta para usuario: {username}")
                return None
            
            # Actualizar último login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Login exitoso: {username}")
            return user
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            raise
    
    @staticmethod
    def get_users_by_role(role: str) -> List[User]:
        """Obtener usuarios por rol"""
        try:
            return User.query.filter_by(role=role).all()
        except Exception as e:
            logger.error(f"Error al obtener usuarios por rol {role}: {e}")
            raise
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> bool:
        """Cambiar contraseña de usuario"""
        try:
            user = UserInterface.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"Usuario {user_id} no encontrado")
            
            # Verificar contraseña actual
            if not check_password_hash(user.password_hash, old_password):
                raise ValueError("Contraseña actual incorrecta")
            
            # Actualizar contraseña
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            logger.info(f"Contraseña cambiada para usuario: {user.username}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al cambiar contraseña: {e}")
            raise
