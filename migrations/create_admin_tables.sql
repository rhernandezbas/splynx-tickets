-- Migration script for admin panel tables
-- Run this script to create the necessary tables for the admin panel

-- Operator Configuration Table
CREATE TABLE IF NOT EXISTS operator_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    whatsapp_number VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_paused BOOLEAN DEFAULT FALSE,
    paused_reason TEXT,
    paused_at DATETIME,
    paused_by VARCHAR(100),
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_person_id (person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Operator Schedule Table
CREATE TABLE IF NOT EXISTS operator_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    day_of_week INT NOT NULL,
    start_time VARCHAR(5) NOT NULL,
    end_time VARCHAR(5) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_person_id (person_id),
    INDEX idx_day_of_week (day_of_week)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- System Configuration Table
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    value_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    category VARCHAR(50),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    INDEX idx_key (`key`),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    old_value JSON,
    new_value JSON,
    performed_by VARCHAR(100),
    performed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),
    notes TEXT,
    INDEX idx_performed_at (performed_at),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default operator configurations from constants
INSERT INTO operator_config (person_id, name, whatsapp_number, is_active, is_paused, notifications_enabled)
VALUES 
    (10, 'Gabriel Romero', '541159300124', TRUE, FALSE, TRUE),
    (27, 'Luis Sarco', '541152596634', TRUE, FALSE, TRUE),
    (37, 'Cesareo Suarez', '542324531873', TRUE, FALSE, TRUE),
    (38, 'Yaini Al', '542324531872', TRUE, FALSE, TRUE)
ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    whatsapp_number = VALUES(whatsapp_number);

-- Insert default schedules (Monday to Friday)
-- Gabriel Romero (10): 08:00 - 16:00
INSERT INTO operator_schedule (person_id, day_of_week, start_time, end_time, is_active)
VALUES 
    (10, 0, '08:00', '16:00', TRUE),
    (10, 1, '08:00', '16:00', TRUE),
    (10, 2, '08:00', '16:00', TRUE),
    (10, 3, '08:00', '16:00', TRUE),
    (10, 4, '08:00', '16:00', TRUE);

-- Luis Sarco (27): 10:00 - 17:20
INSERT INTO operator_schedule (person_id, day_of_week, start_time, end_time, is_active)
VALUES 
    (27, 0, '10:00', '17:20', TRUE),
    (27, 1, '10:00', '17:20', TRUE),
    (27, 2, '10:00', '17:20', TRUE),
    (27, 3, '10:00', '17:20', TRUE),
    (27, 4, '10:00', '17:20', TRUE);

-- Cesareo Suarez (37): 08:00 - 15:00
INSERT INTO operator_schedule (person_id, day_of_week, start_time, end_time, is_active)
VALUES 
    (37, 0, '08:00', '15:00', TRUE),
    (37, 1, '08:00', '15:00', TRUE),
    (37, 2, '08:00', '15:00', TRUE),
    (37, 3, '08:00', '15:00', TRUE),
    (37, 4, '08:00', '15:00', TRUE);

-- Yaini Al (38): 16:00 - 23:00
INSERT INTO operator_schedule (person_id, day_of_week, start_time, end_time, is_active)
VALUES 
    (38, 0, '16:00', '23:00', TRUE),
    (38, 1, '16:00', '23:00', TRUE),
    (38, 2, '16:00', '23:00', TRUE),
    (38, 3, '16:00', '23:00', TRUE),
    (38, 4, '16:00', '23:00', TRUE);

-- Insert default system configurations
INSERT INTO system_config (`key`, value, value_type, description, category)
VALUES 
    ('TICKET_ALERT_THRESHOLD_MINUTES', '60', 'int', 'Tiempo límite en minutos para alertar sobre tickets asignados', 'notifications'),
    ('TICKET_UPDATE_THRESHOLD_MINUTES', '60', 'int', 'Tiempo mínimo desde última actualización para enviar alerta', 'notifications'),
    ('TICKET_RENOTIFICATION_INTERVAL_MINUTES', '60', 'int', 'Intervalo mínimo entre notificaciones del mismo ticket', 'notifications'),
    ('END_OF_SHIFT_NOTIFICATION_MINUTES', '60', 'int', 'Minutos antes del fin de turno para enviar notificación', 'notifications'),
    ('WHATSAPP_ENABLED', 'true', 'bool', 'Habilitar/deshabilitar notificaciones de WhatsApp', 'notifications'),
    ('SYSTEM_PAUSED', 'false', 'bool', 'Pausar/reanudar el sistema completo', 'system'),
    ('OUTHOUSE_NO_ALERT_MINUTES', '120', 'int', 'Minutos sin alerta para tickets en estado OutHouse', 'notifications'),
    ('FINDE_HORA_INICIO', '9', 'int', 'Hora de inicio de trabajo en fin de semana', 'schedules'),
    ('FINDE_HORA_FIN', '21', 'int', 'Hora de fin de trabajo en fin de semana', 'schedules'),
    ('PERSONA_GUARDIA_FINDE', '10', 'int', 'ID de persona de guardia en fin de semana', 'schedules')
ON DUPLICATE KEY UPDATE 
    value = VALUES(value),
    description = VALUES(description);
