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
    closed_at = db.Column(db.DateTime)  # Fecha de cierre del ticket
    is_closed = db.Column(db.Boolean, default=False)  # Indica si el ticket está cerrado
    last_update = db.Column(db.DateTime)  # Última actualización desde Splynx (updated_at)
    recreado = db.Column(db.Integer, default=0)  # Contador de veces que se ha recreado el ticket
    
    # Campos de métricas (unificados desde ticket_response_metrics)
    exceeded_threshold = db.Column(db.Boolean, default=False)  # Si supera el threshold (>60 min)
    response_time_minutes = db.Column(db.Integer)  # Tiempo de respuesta en minutos
    first_alert_sent_at = db.Column(db.DateTime)  # Primera alerta enviada
    last_alert_sent_at = db.Column(db.DateTime)  # Última alerta enviada
    
    # Campos de auditoría
    audit_requested = db.Column(db.Boolean, default=False)  # Operador solicitó auditoría
    audit_notified = db.Column(db.Boolean, default=False)  # Admin fue notificado
    audit_requested_at = db.Column(db.DateTime)  # Fecha de solicitud de auditoría
    audit_requested_by = db.Column(db.Integer)  # Person ID del operador que solicitó
    audit_status = db.Column(db.String(20), default=None)  # None/pending/approved/rejected
    audit_reviewed_at = db.Column(db.DateTime)  # Fecha de revisión por admin
    audit_reviewed_by = db.Column(db.Integer)  # Admin user ID que revisó

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
    is_closed = db.Column(db.Boolean, default=False)  # Indica si el ticket está cerrado
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
    is_paused = db.Column(db.Boolean, default=False)  # Pausa general (todo)
    paused_reason = db.Column(db.Text)
    paused_at = db.Column(db.DateTime)
    paused_by = db.Column(db.String(100))
    notifications_enabled = db.Column(db.Boolean, default=True)  # Pausa de notificaciones
    assignment_paused = db.Column(db.Boolean, default=False)  # Pausa solo asignación de tickets
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<OperatorConfig person_id: {self.person_id}, name: {self.name}, active: {self.is_active}, paused: {self.is_paused}>'


class OperatorSchedule(db.Model):
    """Horarios de trabajo, asignación de tickets y alertas de operadores."""
    __tablename__ = 'operator_schedule'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, nullable=False, index=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Lunes, 6=Domingo
    start_time = db.Column(db.String(5), nullable=False)  # Formato HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # Formato HH:MM
    schedule_type = db.Column(db.String(20), nullable=False, default='work')  # 'work' (horario laboral), 'assignment' (asignación de tickets) o 'alert' (notificaciones WhatsApp)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<OperatorSchedule person_id: {self.person_id}, type: {self.schedule_type}, day: {self.day_of_week}, {self.start_time}-{self.end_time}>'


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


class TicketReassignmentHistory(db.Model):
    """Historial de reasignaciones de tickets"""
    __tablename__ = 'ticket_reassignment_history'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(50), nullable=False, index=True)
    from_operator_id = db.Column(db.Integer)  # Operador anterior (null si era sin asignar)
    from_operator_name = db.Column(db.String(200))
    to_operator_id = db.Column(db.Integer)  # Nuevo operador (null si se desasigna)
    to_operator_name = db.Column(db.String(200))
    reason = db.Column(db.String(500))  # Razón de la reasignación
    reassignment_type = db.Column(db.String(50))  # 'auto_unassign', 'manual', 'end_of_shift', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))  # 'system', 'admin', username
    
    def __repr__(self):
        return f'<TicketReassignment ticket_id: {self.ticket_id}, from: {self.from_operator_id} to: {self.to_operator_id}>'


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
    
    # Permisos de acceso a páginas
    can_access_operator_view = db.Column(db.Boolean, default=True)  # Acceso a vista de operador
    can_access_device_analysis = db.Column(db.Boolean, default=True)  # Acceso a análisis de dispositivos
    
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
            'created_by': self.created_by,
            'can_access_operator_view': self.can_access_operator_view,
            'can_access_device_analysis': self.can_access_device_analysis
        }


class DeviceAnalysis(db.Model):
    """Almacena análisis de dispositivos con respuestas de IA y feedback de usuarios"""
    __tablename__ = 'device_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    device_ip = db.Column(db.String(50), nullable=False, index=True)
    device_name = db.Column(db.String(200))
    device_model = db.Column(db.String(100))
    analysis_type = db.Column(db.String(50), nullable=False)  # 'complete' o 'metrics'
    
    # Datos de la consulta
    query_params = db.Column(JSON)  # Parámetros enviados en la consulta
    
    # Respuesta de la API
    api_response = db.Column(JSON)  # Respuesta completa del endpoint
    llm_summary = db.Column(db.Text)  # Resumen del LLM extraído
    ping_data = db.Column(JSON)  # Datos de ping
    metrics_data = db.Column(JSON)  # Métricas del dispositivo
    site_survey_data = db.Column(JSON)  # Datos de site survey
    
    # Estado de la consulta
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)  # Si hubo error
    execution_time_ms = db.Column(db.Integer)  # Tiempo de ejecución
    
    # Feedback del usuario
    feedback_rating = db.Column(db.String(20))  # 'helpful', 'not_helpful', 'incorrect'
    feedback_comment = db.Column(db.Text)  # Comentario del usuario
    feedback_at = db.Column(db.DateTime)  # Cuándo se dio feedback
    
    # Auditoría
    requested_by = db.Column(db.String(100))  # Usuario que hizo la consulta
    requested_by_role = db.Column(db.String(50))  # 'admin' o 'operator'
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(50))  # IP desde donde se hizo la consulta
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'device_ip': self.device_ip,
            'device_name': self.device_name,
            'device_model': self.device_model,
            'analysis_type': self.analysis_type,
            'query_params': self.query_params,
            'api_response': self.api_response,
            'llm_summary': self.llm_summary,
            'ping_data': self.ping_data,
            'metrics_data': self.metrics_data,
            'site_survey_data': self.site_survey_data,
            'success': self.success,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms,
            'feedback_rating': self.feedback_rating,
            'feedback_comment': self.feedback_comment,
            'feedback_at': self.feedback_at.isoformat() if self.feedback_at else None,
            'requested_by': self.requested_by,
            'requested_by_role': self.requested_by_role,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'ip_address': self.ip_address
        }
    
    def __repr__(self):
        return f'<DeviceAnalysis id: {self.id}, device_ip: {self.device_ip}, type: {self.analysis_type}, success: {self.success}>'