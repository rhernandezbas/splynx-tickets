-- Migración: Crear tabla de usuarios para autenticación
-- Fecha: 2026-01-14

-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    email VARCHAR(200),
    role VARCHAR(50) NOT NULL COMMENT 'admin o operator',
    person_id INT COMMENT 'ID del operador asociado (si es operator)',
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_person_id (person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar usuario admin por defecto
-- Password: admin123 (debe cambiarse en producción)
INSERT INTO users (username, password_hash, full_name, role, is_active, created_by)
VALUES (
    'admin',
    'scrypt:32768:8:1$uZxQYGvXqVKjmEhE$d8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8c8e8f8',
    'Administrador',
    'admin',
    TRUE,
    'system'
) ON DUPLICATE KEY UPDATE username=username;

-- Nota: El hash de arriba es un placeholder. 
-- En el primer deploy, ejecutar este script Python para crear el hash correcto:
-- from werkzeug.security import generate_password_hash
-- print(generate_password_hash('admin123'))
