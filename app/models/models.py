"""This module contains the Incident model."""

from app.utils.config import db
from sqlalchemy.dialects.mysql import JSON
from datetime import datetime


class IncidentsDetection(db.Model):
    """Incidents detection model."""
    __tablename__ = 'tickets_detection'

    id = db.Column(db.BigInteger, primary_key=True)
    Cliente = db.Column(db.String(100))
    Cliente_Nombre = db.Column(db.String(200))
    Asunto = db.Column(db.String(150))
    Fecha_Creacion = db.Column(db.String(100),unique=True)
    Ticket_ID = db.Column(db.Text)
    Estado = db.Column(db.String(100))
    Prioridad = db.Column(db.String(1000))
    is_created_splynx = db.Column(db.Boolean)
    assigned_to = db.Column(db.Integer)


    def __repr__(self):
        return f'<Detection id: {self.id}>'


class AssignmentTracker(db.Model):
    """Tracks ticket assignments per person for fair distribution."""
    __tablename__ = 'assignment_tracker'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, unique=True, nullable=False)
    ticket_count = db.Column(db.Integer, default=0)
    last_assigned = db.Column(db.DateTime)

    def __repr__(self):
        return f'<AssignmentTracker person_id: {self.person_id}, count: {self.ticket_count}>'


class TicketResponseMetrics(db.Model):
    """Tracks response time metrics for tickets that exceed 45 minutes."""
    __tablename__ = 'ticket_response_metrics'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(50), nullable=False, unique=True, index=True)  # UNIQUE constraint
    assigned_to = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.String(100))
    customer_name = db.Column(db.String(200))
    subject = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False)
    first_alert_sent_at = db.Column(db.DateTime)
    last_alert_sent_at = db.Column(db.DateTime)
    response_time_minutes = db.Column(db.Integer)
    alert_count = db.Column(db.Integer, default=0)
    resolved_at = db.Column(db.DateTime)
    exceeded_threshold = db.Column(db.Boolean, default=True)
    auditorado = db.Column(db.Boolean, default=False)  # Campo manual para auditoría
    assignment_history = db.Column(db.JSON, default=list)  # Historial de asignaciones [{assigned_to, assigned_at, reason}]
    
    def __repr__(self):
        return f'<TicketResponseMetrics ticket_id: {self.ticket_id}, assigned_to: {self.assigned_to}, response_time: {self.response_time_minutes}min, auditorado: {self.auditorado}>'


class OperatorConfig(db.Model):
    """Configuración dinámica de operadores."""
    __tablename__ = 'operator_config'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    whatsapp_number = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_paused = db.Column(db.Boolean, default=False)
    paused_reason = db.Column(db.Text)
    paused_at = db.Column(db.DateTime)
    paused_by = db.Column(db.String(100))
    notifications_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<OperatorConfig person_id: {self.person_id}, name: {self.name}, active: {self.is_active}, paused: {self.is_paused}>'


class OperatorSchedule(db.Model):
    """Horarios de trabajo de operadores."""
    __tablename__ = 'operator_schedule'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, nullable=False, index=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Lunes, 6=Domingo
    start_time = db.Column(db.String(5), nullable=False)  # Formato HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # Formato HH:MM
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<OperatorSchedule person_id: {self.person_id}, day: {self.day_of_week}, {self.start_time}-{self.end_time}>'


class SystemConfig(db.Model):
    """Configuración global del sistema."""
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20), default='string')  # string, int, bool, json
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # notifications, schedules, thresholds, etc.
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    updated_by = db.Column(db.String(100))

    def __repr__(self):
        return f'<SystemConfig key: {self.key}, value: {self.value}>'


class AuditLog(db.Model):
    """Registro de auditoría de cambios en el sistema."""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.String(100))
    old_value = db.Column(JSON)
    new_value = db.Column(JSON)
    performed_by = db.Column(db.String(100))
    performed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    notes = db.Column(db.Text)


class MessageTemplate(db.Model):
    __tablename__ = 'message_template'
    
    id = db.Column(db.Integer, primary_key=True)
    template_key = db.Column(db.String(100), unique=True, nullable=False)
    template_name = db.Column(db.String(200), nullable=False)
    template_content = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    variables = db.Column(JSON)  # Lista de variables disponibles
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100))

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'template_key': self.template_key,
            'template_name': self.template_name,
            'template_content': self.template_content,
            'description': self.description,
            'variables': self.variables,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }

    def __repr__(self):
        return f'<MessageTemplate template_key: {self.template_key}, template_name: {self.template_name}>'


class User(db.Model):
    """Modelo de usuarios para autenticación"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    role = db.Column(db.String(50), nullable=False)  # 'admin' o 'operator'
    person_id = db.Column(db.Integer)  # ID del operador asociado (si es operator)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    def to_dict(self):
        """Convert to dictionary (sin password)"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'person_id': self.person_id,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }