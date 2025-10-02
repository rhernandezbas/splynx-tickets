"""This module contains the Incident model."""

from app.utils.config import db


class IncidentsDetection(db.Model):
    """Incidents detection model."""
    __tablename__ = 'tickets_detection'

    id = db.Column(db.BigInteger, primary_key=True)
    Cliente = db.Column(db.String(100))
    Asunto = db.Column(db.String(150))
    Fecha_Creacion = db.Column(db.String(100))
    Ticket_ID = db.Column(db.Text)
    Estado = db.Column(db.String(100))
    Prioridad = db.Column(db.String(1000))
    is_created_splynx = db.Column(db.Boolean)


    def __repr__(self):
        return f'<Detection id: {self.id}>'