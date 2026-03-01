"""
Job para verificar tickets en ventana de reapertura.
Si un ticket fue cerrado en Splynx pero no en GR dentro de la ventana configurada,
se reabre automáticamente en Splynx y se notifica al operador.
"""

from app.utils.config import db
from app.models.models import IncidentsDetection
from app.services.splynx_services_singleton import SplynxServicesSingleton
from app.utils.config_helper import ConfigHelper
from app.utils.logger import get_logger
from app.interface.webhook_interface import HookCierreTicketInterface
from datetime import datetime
import pytz

logger = get_logger(__name__)

ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')


def check_and_reopen_tickets():
    """
    Revisa tickets con splynx_closed_at NOT NULL y is_closed = False.
    Si la ventana expiró sin cierre de GR, reabre el ticket en Splynx.
    Si hay cierre de GR, cierra normalmente.
    """
    try:
        window_minutes = ConfigHelper.get_int('TICKET_REOPEN_WINDOW_MINUTES', 7)

        # Tickets en ventana de reapertura
        tickets_in_window = IncidentsDetection.query.filter(
            IncidentsDetection.splynx_closed_at.isnot(None),
            IncidentsDetection.is_closed == False
        ).all()

        if not tickets_in_window:
            logger.debug("🔍 No hay tickets en ventana de reapertura")
            return {'checked': 0, 'reopened': 0, 'closed': 0}

        logger.info(f"🔍 Verificando {len(tickets_in_window)} tickets en ventana de reapertura (ventana: {window_minutes} min)")

        now = datetime.now(ARGENTINA_TZ).replace(tzinfo=None)
        reopened_count = 0
        closed_count = 0

        for ticket in tickets_in_window:
            try:
                elapsed = (now - ticket.splynx_closed_at).total_seconds() / 60

                if elapsed < window_minutes:
                    logger.debug(f"⏳ Ticket {ticket.Ticket_ID}: {elapsed:.1f} min en ventana ({window_minutes} min requeridos)")
                    continue

                # Ventana expirada - verificar si hay cierre de GR
                gr_closure = None
                if ticket.numero_ticket_gr:
                    gr_closure = HookCierreTicketInterface.find_by_numero_ticket(ticket.numero_ticket_gr)

                if gr_closure:
                    # Caso 2: Cierre de GR llegó durante la ventana → cerrar normalmente
                    ticket.is_closed = True
                    ticket.closed_at = datetime.now()
                    ticket.splynx_closed_at = None

                    if ticket.Estado not in ('SUCCESS', 'CLOSED'):
                        ticket.Estado = 'CLOSED'

                    closed_count += 1
                    logger.info(f"✅ Ticket {ticket.Ticket_ID} cerrado normalmente (cierre GR encontrado dentro de ventana)")
                else:
                    # Caso 1: Sin cierre de GR → reabrir en Splynx
                    _reopen_ticket(ticket)
                    reopened_count += 1

            except Exception as e:
                logger.error(f"❌ Error procesando ticket {ticket.Ticket_ID} en reopen checker: {e}")
                continue

        db.session.commit()
        logger.info(f"🔄 Reopen checker completado: {reopened_count} reabiertos, {closed_count} cerrados normalmente")

        return {
            'checked': len(tickets_in_window),
            'reopened': reopened_count,
            'closed': closed_count,
        }

    except Exception as e:
        logger.error(f"❌ Error en ticket reopen checker: {e}")
        db.session.rollback()
        return {'checked': 0, 'reopened': 0, 'closed': 0, 'error': str(e)}


def _reopen_ticket(ticket):
    """Reabre un ticket en Splynx y notifica al operador."""
    ticket_id = ticket.Ticket_ID

    # Reabrir en Splynx
    splynx = SplynxServicesSingleton()
    result = splynx.reopen_ticket(ticket_id)

    if not result:
        logger.error(f"❌ No se pudo reabrir ticket {ticket_id} en Splynx")
        return

    # Actualizar estado local
    ticket.recreado = (ticket.recreado or 0) + 1
    ticket.splynx_closed_at = None
    logger.info(f"🔄 Ticket {ticket_id} reabierto en Splynx (recreado={ticket.recreado}) - sin cierre en GR")

    # Notificar al operador por WhatsApp
    if ticket.assigned_to and ConfigHelper.is_whatsapp_enabled():
        try:
            from app.services.whatsapp_service import WhatsAppService
            whatsapp = WhatsAppService()
            whatsapp.send_ticket_reopened(
                person_id=ticket.assigned_to,
                ticket_id=ticket_id,
                subject=ticket.Asunto or 'Sin asunto',
                customer_name=ticket.Cliente_Nombre or 'Cliente desconocido'
            )
        except Exception as e:
            logger.warning(f"⚠️ No se pudo enviar notificación de reapertura para ticket {ticket_id}: {e}")
