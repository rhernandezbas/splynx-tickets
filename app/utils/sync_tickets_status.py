"""
Job para sincronizar el estado de tickets con Splynx
Verifica si tickets están cerrados en Splynx y actualiza la BD local
Calcula exceeded_threshold y response_time_minutes
"""

from app.utils.config import db
from app.models.models import IncidentsDetection
from app.services.splynx_services import SplynxServices
from app.utils.config_helper import ConfigHelper
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

# Timezone de Argentina
ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def parse_date(date_str):
    """Parse DD-MM-YYYY HH:MM:SS format to datetime"""
    if not date_str:
        return None
    try:
        parts = date_str.split(' ')
        date_parts = parts[0].split('-')
        time_part = parts[1] if len(parts) > 1 else '00:00:00'
        year = date_parts[2]
        month = date_parts[1]
        day = date_parts[0]
        return datetime.strptime(f'{year}-{month}-{day} {time_part}', '%Y-%m-%d %H:%M:%S')
    except:
        return None

def sync_tickets_status():
    """
    Sincroniza el estado de tickets abiertos con Splynx.
    Actualiza: is_closed, closed_at, exceeded_threshold, response_time_minutes
    """
    try:
        splynx = SplynxServices()
        
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
                    
                    # Calcular tiempo desde última actualización (no desde creación)
                    # Si el ticket fue respondido/actualizado, el contador se resetea
                    last_update = None
                    if updated_at:
                        try:
                            last_update = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                            # Guardar last_update en BD
                            ticket.last_update = last_update
                        except ValueError:
                            last_update = None
                    
                    # Si no hay updated_at, usar fecha de creación como fallback
                    if not last_update:
                        last_update = parse_date(ticket.Fecha_Creacion)
                        # Si usamos Fecha_Creacion, también guardarlo en last_update si no existe
                        if last_update and not ticket.last_update:
                            ticket.last_update = last_update
                    
                    if last_update:
                        # Usar hora de Argentina para el cálculo
                        now_argentina = datetime.now(ARGENTINA_TZ)
                        
                        # Si last_update no tiene timezone, asumimos que es Argentina
                        if last_update.tzinfo is None:
                            last_update = ARGENTINA_TZ.localize(last_update)
                        
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
                        
                        # Marcar como cerrado
                        ticket.is_closed = True
                        ticket.exceeded_threshold = False  # Los cerrados no están vencidos
                        
                        # Actualizar estado basado en status_id
                        if status_id == '3':
                            ticket.Estado = 'SUCCESS'
                        else:
                            ticket.Estado = 'CLOSED'
                        
                        closed_count += 1
                        logger.info(f"✅ Ticket {ticket_id} marcado como cerrado (closed=1, is_closed=True, status_id={status_id}, updated_at={updated_at})")
                    else:
                        # Ticket aún abierto
                        ticket.is_closed = False
                        logger.debug(f"ℹ️  Ticket {ticket_id} aún abierto (closed=0, response_time={ticket.response_time_minutes}min, exceeded={ticket.exceeded_threshold})")
                        
            except Exception as e:
                logger.error(f"❌ Error al sincronizar ticket {ticket.Ticket_ID}: {e}")
                continue
        
        db.session.commit()
        logger.info(f"✅ Sincronización completada: {closed_count} tickets cerrados, {exceeded_count} tickets vencidos")
        
        return {
            'success': True,
            'total_checked': len(open_tickets),
            'closed_count': closed_count,
            'exceeded_count': exceeded_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error en sincronización de tickets: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }
