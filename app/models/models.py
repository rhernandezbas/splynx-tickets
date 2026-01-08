"""This module contains the Incident model."""

from app.utils.config import db


class IncidentsDetection(db.Model):
    """Incidents detection model."""
    __tablename__ = 'tickets_detection'

    id = db.Column(db.BigInteger, primary_key=True)
    Cliente = db.Column(db.String(100))
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