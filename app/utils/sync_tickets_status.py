"""
Job para sincronizar el estado de tickets con Splynx
Verifica si tickets están cerrados en Splynx y actualiza la BD local
Calcula exceeded_threshold y response_time_minutes
Sincroniza assigned_to y registra cambios en historial de reasignaciones
OPTIMIZADO: Usa SplynxServicesSingleton para evitar múltiples logins
"""

from app.utils.config import db
from app.models.models import IncidentsDetection
from app.services.splynx_services_singleton import SplynxServicesSingleton
from app.utils.config_helper import ConfigHelper
from app.utils.date_utils import parse_ticket_date, parse_splynx_date, ensure_argentina_tz
from app.utils.logger import get_logger
from app.interface.reassignment_history import ReassignmentHistoryInterface
from app.interface.interfaces import OperatorConfigInterface
from datetime import datetime
import pytz

logger = get_logger(__name__)

# Timezone de Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')


def _get_operator_name(person_id):
    """Resuelve nombre del operador desde operator_config."""
    if not person_id:
        return 'Sin asignar'
    op = OperatorConfigInterface.get_by_person_id(person_id)
    return op.name if op else f'Operador {person_id}'


def sync_tickets_status():
    """
    Sincroniza el estado de tickets abiertos con Splynx.
    Actualiza: is_closed, closed_at, exceeded_threshold, response_time_minutes, assigned_to
    Registra cambios de asignación en historial de reasignaciones.
    """
    try:
        splynx = SplynxServicesSingleton()
        
        # Obtener threshold desde configuración (default 60 minutos)
        threshold_minutes = ConfigHelper.get_int('TICKET_ALERT_THRESHOLD_MINUTES', 60)
        
        # Obtener todos los tickets abiertos usando is_closed
        open_tickets = IncidentsDetection.query.filter(
            IncidentsDetection.is_closed == False,
            IncidentsDetection.Ticket_ID.isnot(None)
        ).all()
        
        logger.info(f"🔄 Sincronizando {len(open_tickets)} tickets abiertos con Splynx (threshold: {threshold_minutes} min)...")
        
        closed_count = 0
        exceeded_count = 0
        reassigned_count = 0
        
        for ticket in open_tickets:
            try:
                # Obtener el estado actual del ticket en Splynx
                ticket_id = ticket.Ticket_ID
                if not ticket_id:
                    continue
                
                # Consultar ticket en Splynx
                splynx_ticket = splynx.get_ticket_data_status(ticket_id)
                
                if splynx_ticket:
                    # Usar el campo 'closed' de la respuesta de Splynx
                    is_closed = splynx_ticket.get('closed', '0') == '1'
                    status_id = splynx_ticket.get('status_id', '')
                    updated_at = splynx_ticket.get('updated_at', '')
                    # IMPORTANTE: La API de Splynx usa 'assign_to' no 'assigned_to'
                    assigned_to_splynx = splynx_ticket.get('assign_to', None) or splynx_ticket.get('assigned_to', None)
                    
                    # Sincronizar assigned_to desde Splynx
                    if assigned_to_splynx:
                        # Convertir a int si no es None
                        new_assigned_to = int(assigned_to_splynx) if assigned_to_splynx else None
                    else:
                        new_assigned_to = None

                    # Sincronizar assigned_to si cambió en Splynx
                    if new_assigned_to is not None and new_assigned_to != ticket.assigned_to:
                        old_assigned_to = ticket.assigned_to
                        ticket.assigned_to = new_assigned_to

                        old_name = _get_operator_name(old_assigned_to)
                        new_name = _get_operator_name(new_assigned_to)

                        ReassignmentHistoryInterface.create({
                            'ticket_id': str(ticket_id),
                            'from_operator_id': old_assigned_to,
                            'from_operator_name': old_name,
                            'to_operator_id': new_assigned_to,
                            'to_operator_name': new_name,
                            'reason': 'Cambio detectado en Splynx durante sincronización',
                            'reassignment_type': 'splynx_sync',
                            'created_by': 'system'
                        })
                        reassigned_count += 1
                        logger.info(f"🔄 Ticket {ticket_id}: reasignado {old_name} ({old_assigned_to}) → {new_name} ({new_assigned_to})")

                    # Calcular tiempo desde última actualización (no desde creación)
                    # Si el ticket fue respondido/actualizado, el contador se resetea
                    last_update = None

                    # Usar updated_at de Splynx como fuente de última actualización
                    if updated_at:
                        last_update = parse_splynx_date(updated_at)
                        if last_update:
                            ticket.last_update = last_update
                            logger.debug(f"*** Ticket {ticket_id}: Usando updated_at: {last_update}")

                    # Si no hay last_update aún, usar fecha de creación como fallback
                    if not last_update:
                        last_update = parse_ticket_date(ticket.Fecha_Creacion)
                        if last_update and not ticket.last_update:
                            ticket.last_update = last_update
                            logger.debug(f"*** Ticket {ticket_id}: Fallback a Fecha_Creacion: {last_update}")
                    
                    if last_update:
                        # Usar hora de Argentina para el cálculo
                        now_argentina = datetime.now(ARGENTINA_TZ)

                        # Asegurar que last_update tenga timezone Argentina
                        last_update = ensure_argentina_tz(last_update)

                        # Calcular tiempo transcurrido en minutos
                        time_since_update = int((now_argentina - last_update).total_seconds() / 60)
                        ticket.response_time_minutes = time_since_update
                        
                        # IMPORTANTE: exceeded_threshold persiste una vez activado
                        # Solo se puede desactivar cuando el ticket se cierra
                        if not is_closed:
                            # Si ya estaba vencido, mantenerlo vencido
                            if ticket.exceeded_threshold:
                                exceeded_count += 1
                            # Si no estaba vencido, verificar si ahora excede el threshold
                            elif time_since_update > threshold_minutes:
                                ticket.exceeded_threshold = True
                                exceeded_count += 1
                                logger.info(f"🔴 Ticket {ticket_id} marcado como VENCIDO (response_time={time_since_update}min > {threshold_minutes}min)")
                        # Si está cerrado, se manejará más abajo
                    
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

                        # Calcular tiempo total de resolución (creación → cierre)
                        if ticket.closed_at and ticket.Fecha_Creacion:
                            created_at = parse_ticket_date(ticket.Fecha_Creacion)
                            if created_at:
                                # Asegurar que closed_at tenga timezone Argentina
                                closed_at_tz = ensure_argentina_tz(ticket.closed_at)
                                created_at_tz = ensure_argentina_tz(created_at)

                                # Calcular diferencia en minutos
                                resolution_time = int((closed_at_tz - created_at_tz).total_seconds() / 60)
                                ticket.resolution_time_minutes = resolution_time
                                logger.debug(f"📊 Ticket {ticket_id}: Tiempo de resolución calculado: {resolution_time} minutos")

                        # Marcar como cerrado
                        ticket.is_closed = True
                        # IMPORTANTE: NO resetear exceeded_threshold al cerrar
                        # Mantener el valor para cálculo de SLA y observabilidad
                        # Si estuvo vencido, debe permanecer vencido para las métricas

                        # Actualizar estado basado en status_id
                        if status_id == '3':
                            ticket.Estado = 'SUCCESS'
                        else:
                            ticket.Estado = 'CLOSED'

                        closed_count += 1
                        logger.info(f"✅ Ticket {ticket_id} marcado como cerrado (closed=1, is_closed=True, exceeded_threshold={ticket.exceeded_threshold}, resolution_time={ticket.resolution_time_minutes}min, status_id={status_id})")
                    else:
                        # Ticket aún abierto
                        ticket.is_closed = False
                        logger.debug(f"ℹ️  Ticket {ticket_id} aún abierto (closed=0, response_time={ticket.response_time_minutes}min, exceeded={ticket.exceeded_threshold})")
                        
            except Exception as e:
                logger.error(f"❌ Error al sincronizar ticket {ticket.Ticket_ID}: {e}")
                continue
        
        db.session.commit()
        logger.info(f"✅ Sincronización completada: {closed_count} cerrados, {exceeded_count} vencidos, {reassigned_count} reasignados")

        return {
            'success': True,
            'total_checked': len(open_tickets),
            'closed_count': closed_count,
            'exceeded_count': exceeded_count,
            'reassigned_count': reassigned_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error en sincronización de tickets: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }
