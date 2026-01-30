"""
Importa tickets existentes del grupo 4 de Splynx a la BD local
Se ejecuta periódicamente para asegurar que todos los tickets activos estén en BD
OPTIMIZADO: Usa SplynxServicesSingleton para evitar múltiples logins
"""

from app.utils.config import db
from app.models.models import IncidentsDetection
from app.services.splynx_services_singleton import SplynxServicesSingleton
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def parse_splynx_date(date_str):
    """Parse fecha de Splynx (YYYY-MM-DD HH:MM:SS) a formato DD-MM-YYYY HH:MM:SS"""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d-%m-%Y %H:%M:%S')
    except:
        return None

def import_existing_tickets_from_splynx():
    """
    Importa todos los tickets activos (no cerrados) del grupo 4 de Splynx a la BD.
    Solo importa tickets que no existan ya en la BD.
    """
    try:
        splynx = SplynxServicesSingleton()
        
        # Obtener tickets asignados y no asignados del grupo 4
        logger.info("📥 Importando tickets existentes del grupo 4 desde Splynx...")
        
        unassigned_tickets = splynx.get_unassigned_tickets(group_id="4")
        assigned_tickets = splynx.get_assigned_tickets(group_id="4")
        
        all_tickets = unassigned_tickets + assigned_tickets
        logger.info(f"📊 Encontrados {len(all_tickets)} tickets activos en Splynx (grupo 4)")
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for ticket in all_tickets:
            try:
                ticket_id = str(ticket.get('id', ''))
                if not ticket_id:
                    continue
                
                # Verificar si el ticket ya existe en BD
                existing = IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Extraer datos del ticket
                customer_id = ticket.get('customer_id', '')
                customer_name = ticket.get('customer_name', 'N/A')
                subject = ticket.get('subject', 'Sin asunto')
                status_id = ticket.get('status_id', '1')
                priority_id = ticket.get('priority_id', '2')
                # IMPORTANTE: La API de Splynx usa 'assign_to' no 'assigned_to'
                assigned_to = ticket.get('assign_to', None) or ticket.get('assigned_to', None)
                created_at = ticket.get('created_at', '')
                closed = ticket.get('closed', '0')
                
                # Convertir fecha
                fecha_creacion = parse_splynx_date(created_at)
                if not fecha_creacion:
                    fecha_creacion = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                
                # Mapear prioridad
                priority_map = {'1': 'Baja', '2': 'Media', '3': 'Alta', '4': 'Crítica'}
                prioridad = priority_map.get(str(priority_id), 'Media')
                
                # Mapear estado
                if closed == '1':
                    estado = 'SUCCESS' if status_id == '3' else 'CLOSED'
                    is_closed = True
                else:
                    estado = 'OPEN'
                    is_closed = False
                
                # Crear registro en BD
                incident_data = {
                    'Cliente': customer_id,
                    'Cliente_Nombre': customer_name,
                    'Asunto': subject,
                    'Fecha_Creacion': fecha_creacion,
                    'Ticket_ID': ticket_id,
                    'Estado': estado,
                    'Prioridad': prioridad,
                    'is_created_splynx': True,  # Ya existe en Splynx
                    'assigned_to': int(assigned_to) if assigned_to else None,
                    'is_closed': is_closed
                }
                
                from app.interface.interfaces import IncidentsInterface
                incident = IncidentsInterface.create(incident_data)
                
                if incident:
                    imported_count += 1
                    logger.info(f"✅ Ticket {ticket_id} importado: {customer_name} - {subject}")
                else:
                    error_count += 1
                    logger.warning(f"⚠️ No se pudo importar ticket {ticket_id}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error importando ticket {ticket.get('id', 'N/A')}: {e}")
                continue
        
        logger.info(f"✅ Importación completada: {imported_count} importados, {skipped_count} ya existían, {error_count} errores")
        
        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_checked': len(all_tickets)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en importación de tickets: {e}")
        return {
            'success': False,
            'error': str(e)
        }
