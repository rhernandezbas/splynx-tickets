"""
Job para sincronizar el estado de tickets con Splynx
Verifica si tickets están cerrados en Splynx y actualiza la BD local
"""

from app.utils.config import db
from app.models.models import IncidentsDetection
from app.utils.splynx_api import SplynxAPI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def sync_tickets_status():
    """
    Sincroniza el estado de tickets abiertos con Splynx.
    Si un ticket está cerrado en Splynx, actualiza closed_at en la BD.
    """
    try:
        splynx = SplynxAPI()
        
        # Obtener todos los tickets que no tienen closed_at (tickets abiertos en nuestra BD)
        open_tickets = IncidentsDetection.query.filter(
            IncidentsDetection.closed_at.is_(None),
            IncidentsDetection.Ticket_ID.isnot(None)
        ).all()
        
        logger.info(f"🔄 Sincronizando {len(open_tickets)} tickets abiertos con Splynx...")
        
        closed_count = 0
        
        for ticket in open_tickets:
            try:
                # Obtener el estado actual del ticket en Splynx
                ticket_id = ticket.Ticket_ID
                if not ticket_id:
                    continue
                
                # Consultar ticket en Splynx
                splynx_ticket = splynx.get_ticket(ticket_id)
                
                if splynx_ticket:
                    # Usar el campo 'closed' de la respuesta de Splynx
                    is_closed = splynx_ticket.get('closed', '0') == '1'
                    status_id = splynx_ticket.get('status_id', '')
                    updated_at = splynx_ticket.get('updated_at', '')
                    
                    # Si el ticket está cerrado en Splynx (closed = "1")
                    if is_closed:
                        # Usar updated_at de Splynx como fecha de cierre
                        if updated_at:
                            try:
                                ticket.closed_at = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                ticket.closed_at = datetime.now()
                        else:
                            ticket.closed_at = datetime.now()
                        
                        # Actualizar estado basado en status_id
                        if status_id == '3':
                            ticket.Estado = 'SUCCESS'
                        else:
                            ticket.Estado = 'CLOSED'
                        
                        closed_count += 1
                        logger.info(f"✅ Ticket {ticket_id} marcado como cerrado (closed=1, status_id={status_id}, updated_at={updated_at})")
                    else:
                        # Ticket aún abierto, actualizar status_id si cambió
                        logger.debug(f"ℹ️  Ticket {ticket_id} aún abierto (closed=0, status_id={status_id})")
                        
            except Exception as e:
                logger.error(f"❌ Error al sincronizar ticket {ticket.Ticket_ID}: {e}")
                continue
        
        db.session.commit()
        logger.info(f"✅ Sincronización completada: {closed_count} tickets cerrados")
        
        return {
            'success': True,
            'total_checked': len(open_tickets),
            'closed_count': closed_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error en sincronización de tickets: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }
