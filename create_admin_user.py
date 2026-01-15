#!/usr/bin/env python3
"""
Script para crear el usuario admin inicial
"""

from werkzeug.security import generate_password_hash
import pymysql
import os

# Configuración de la base de datos
DB_HOST = os.getenv('DB_HOST', '190.7.234.37')
DB_PORT = int(os.getenv('DB_PORT', 3025))
DB_USER = os.getenv('DB_USER', 'mysql')
DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')
DB_NAME = os.getenv('DB_NAME', 'ipnext')

# Credenciales del admin
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'  # Cambiar en producción
ADMIN_FULL_NAME = 'Administrador'

def create_admin_user():
    """Crear usuario admin en la base de datos"""
    try:
        # Conectar a la base de datos
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✅ Conectado a la base de datos {DB_NAME}")
        
        with connection.cursor() as cursor:
            # Generar hash de la contraseña
            password_hash = generate_password_hash(ADMIN_PASSWORD)
            print(f"✅ Hash generado para contraseña")
            
            # Insertar o actualizar usuario admin
            sql = """
                INSERT INTO users (username, password_hash, full_name, role, is_active, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    password_hash = VALUES(password_hash),
                    full_name = VALUES(full_name),
                    is_active = VALUES(is_active)
            """
            cursor.execute(sql, (
                ADMIN_USERNAME,
                password_hash,
                ADMIN_FULL_NAME,
                'admin',
                True,
                'system'
            ))
            
            connection.commit()
            print(f"✅ Usuario admin creado/actualizado exitosamente")
            print(f"   Username: {ADMIN_USERNAME}")
            print(f"   Password: {ADMIN_PASSWORD}")
            print(f"   ⚠️  IMPORTANTE: Cambiar la contraseña después del primer login")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    create_admin_user()
