"""Repository interfaces for incoming webhook data."""

from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError

from app.utils.config import db
from app.models.models import HookNuevoTicket, HookCierreTicket
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HookNuevoTicketInterface:
    """Repository for HookNuevoTicket model."""

    @staticmethod
    def create(data: dict) -> Optional[HookNuevoTicket]:
        """Save a new-ticket webhook payload to the database."""
        try:
            record = HookNuevoTicket(
                nombre_empresa=data.get('nombre_empresa'),
                numero_ticket=data.get('numero_ticket'),
                fecha_creado=data.get('fecha_creado'),
                departamento=data.get('departamento'),
                canal_entrada=data.get('canal_entrada'),
                motivo_contacto=data.get('motivo_contacto'),
                numero_cliente=data.get('numero_cliente'),
                numero_whatsapp=data.get('numero_whatsapp'),
                nombre_usuario=data.get('nombre_usuario'),
            )
            db.session.add(record)
            db.session.commit()
            return record
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error saving HookNuevoTicket: {e}")
            return None

    @staticmethod
    def get_all() -> List[HookNuevoTicket]:
        """Return all new-ticket webhook records."""
        return HookNuevoTicket.query.order_by(HookNuevoTicket.received_at.desc()).all()

    @staticmethod
    def get_by_numero_ticket(numero: int) -> List[HookNuevoTicket]:
        """Return all records for a given ticket number."""
        return HookNuevoTicket.query.filter_by(numero_ticket=numero).order_by(HookNuevoTicket.received_at.desc()).all()


    @staticmethod
    def get_unprocessed() -> List[HookNuevoTicket]:
        """Return all unprocessed new-ticket webhook records, oldest first."""
        try:
            return HookNuevoTicket.query.filter_by(processed=False).order_by(HookNuevoTicket.received_at.asc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting unprocessed HookNuevoTicket: {e}")
            return []

    @staticmethod
    def mark_processed(record_id: int) -> bool:
        """Mark a webhook record as processed."""
        try:
            from datetime import datetime
            record = HookNuevoTicket.query.get(record_id)
            if not record:
                return False
            record.processed = True
            record.processed_at = datetime.utcnow()
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error marking HookNuevoTicket {record_id} as processed: {e}")
            return False


class HookCierreTicketInterface:
    """Repository for HookCierreTicket model."""

    @staticmethod
    def create(data: dict) -> Optional[HookCierreTicket]:
        """Save a ticket-closure webhook payload to the database."""
        try:
            record = HookCierreTicket(
                nombre_empresa=data.get('nombre_empresa'),
                numero_ticket=data.get('numero_ticket'),
                fecha_creado=data.get('fecha_creado'),
                fecha_cerrado=data.get('fecha_cerrado'),
                asignado=data.get('asignado'),
                descripcion_cierre=data.get('descripcion_cierre'),
                motivo=data.get('motivo'),
                tiempo_vida_ticket=data.get('tiempo_vida_ticket'),
                tiempo_trabajo_real=data.get('tiempo_trabajo_real'),
                tiempo_reaccion=data.get('tiempo_reaccion'),
                departamento=data.get('departamento'),
                canal_entrada=data.get('canal_entrada'),
                motivo_contacto=data.get('motivo_contacto'),
                numero_cliente=data.get('numero_cliente'),
                numero_whatsapp=data.get('numero_whatsapp'),
                nombre_usuario=data.get('nombre_usuario'),
            )
            db.session.add(record)
            db.session.commit()
            return record
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error saving HookCierreTicket: {e}")
            return None

    @staticmethod
    def get_all() -> List[HookCierreTicket]:
        """Return all ticket-closure webhook records."""
        return HookCierreTicket.query.order_by(HookCierreTicket.received_at.desc()).all()
