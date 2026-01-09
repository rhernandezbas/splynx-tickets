"""This module contains the Incident model."""

from app.utils.config import db


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