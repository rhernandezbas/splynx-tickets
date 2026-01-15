-- Agregar columna schedule_type a operator_schedule
ALTER TABLE operator_schedule 
ADD COLUMN schedule_type VARCHAR(20) NOT NULL DEFAULT 'alert' AFTER end_time;

-- Actualizar registros existentes para que sean de tipo 'alert' (los horarios actuales)
UPDATE operator_schedule SET schedule_type = 'alert' WHERE schedule_type IS NULL OR schedule_type = '';

-- Crear índice para mejorar consultas por tipo de horario
CREATE INDEX idx_schedule_type ON operator_schedule(person_id, schedule_type);
