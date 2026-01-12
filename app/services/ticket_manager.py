"""
Ticket Manager - Handles ticket filtering and cleanup operations
Separates business logic from API calls
"""


from app.services.splynx_services import SplynxServices
from app.services.whatsapp_service import WhatsAppService
from app.interface.interfaces import TicketResponseMetricsInterface
from datetime import datetime
import pytz
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TicketManager:
    """Manages ticket operations including filtering and cleanup"""
    
    ASSIGNABLE_PERSONS = [10, 27, 37, 38]

    def __init__(self, splynx_service: SplynxServices):
        """
        Initialize the ticket manager

        Args:
            splynx_service: An instance of SplynxServices
        """
        self.splynx = splynx_service
        self.whatsapp = WhatsAppService()
    
    def get_next_assignee(self, ticket_note: str = None) -> int:
        """Obtiene la siguiente persona a asignar según horario y round-robin, SIN incrementar contador.
        
        Si la nota del ticket contiene etiquetas especiales, asigna según turno:
        - [TT] = Turno Tarde -> IDs 27, 38 (Luis, Yaini)
        - [TD] = Turno Día -> IDs 10, 37 (Gabriel, Cesareo)
        
        Fin de semana (sábado y domingo):
        - Solo persona de guardia (ID 10) de 9:00 AM a 9:00 PM
        
        Turnos normales (lunes a viernes):
        - ID 10: 8:00 AM - 4:00 PM
        - ID 27: 10:00 AM - 5:20 PM
        - ID 37: 8:00 AM - 3:00 PM
        - ID 38: 5:00 PM - 11:00 PM
        
        NOTA: Entre 12:00 AM - 8:00 AM nadie trabaja, tickets se asignan pero no se cuentan
        como tiempo laboral hasta las 8:00 AM
        
        Args:
            ticket_note: Nota del ticket para verificar etiquetas [TT] o [TD]
        
        Returns:
            int: ID de la persona a asignar según el horario o etiqueta
        """
        from app.interface.interfaces import AssignmentTrackerInterface
        from app.utils.constants import TURNO_TARDE_IDS, TURNO_DIA_IDS, PERSONA_GUARDIA_FINDE, FINDE_HORA_INICIO, FINDE_HORA_FIN
        
        # Obtener hora actual en Argentina
        tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
        now = datetime.now(tz_argentina)
        current_hour = now.hour
        current_minute = now.minute
        current_time_minutes = current_hour * 60 + current_minute
        day_of_week = now.weekday()  # 0=Lunes, 6=Domingo
        
        # Verificar si es fin de semana (sábado=5, domingo=6)
        if day_of_week >= 5:
            # Fin de semana: solo asignar a persona de guardia en horario 9-21hs
            if FINDE_HORA_INICIO <= current_hour < FINDE_HORA_FIN:
                logger.info(f"📅 Fin de semana - Asignando a persona de guardia (ID {PERSONA_GUARDIA_FINDE}) - {current_hour}:{current_minute:02d}")
                return PERSONA_GUARDIA_FINDE
            else:
                logger.warning(f"⚠️  Fin de semana fuera de horario ({current_hour}:{current_minute:02d}). Horario: {FINDE_HORA_INICIO}:00-{FINDE_HORA_FIN}:00")
                return PERSONA_GUARDIA_FINDE  # Asignar igual a guardia pero fuera de horario
        
        # Verificar si hay etiqueta de turno en la nota (solo días laborables)
        if ticket_note:
            if "[TT]" in ticket_note:
                # Turno Tarde: asignar a Luis (27) o Yaini (38)
                person_id = AssignmentTrackerInterface.get_person_with_least_tickets(TURNO_TARDE_IDS)
                logger.info(f"🏷️  Etiqueta [TT] detectada - Asignando a turno tarde: {person_id}")
                return person_id
            elif "[TD]" in ticket_note:
                # Turno Día: asignar a Gabriel (10) o Cesareo (37)
                person_id = AssignmentTrackerInterface.get_person_with_least_tickets(TURNO_DIA_IDS)
                logger.info(f"🏷️  Etiqueta [TD] detectada - Asignando a turno día: {person_id}")
                return person_id
        
        # Lógica normal por horario (lunes a viernes)
        
        # Definir horarios en minutos desde medianoche
        # ID 10: 8:00 AM (480) - 4:00 PM (960)
        # ID 27: 10:00 AM (600) - 5:20 PM (1040)
        # ID 37: 8:00 AM (480) - 3:00 PM (900)
        # ID 38: 4:00 PM (960) - 11:00 PM (1380)
        
        available_persons = []
        
        # Verificar quién está disponible según el horario diurno
        if 480 <= current_time_minutes < 900:  # 8:00 AM - 3:00 PM
            available_persons.append(37)
        
        if 480 <= current_time_minutes < 960:  # 8:00 AM - 4:00 PM
            available_persons.append(10)
        
        if 600 <= current_time_minutes < 1040:  # 10:00 AM - 5:20 PM
            available_persons.append(27)
        
        if 960 <= current_time_minutes <= 1380:  # 4:00 PM - 11:00 PM
            available_persons.append(38)
        
        # Si no hay nadie disponible, usar fallback (round-robin entre todos)
        if not available_persons:
            logger.warning(f"⚠️  Fuera de horario laboral ({current_hour}:{current_minute:02d}). Usando asignación round-robin.")
            person_id = AssignmentTrackerInterface.get_person_with_least_tickets(
                self.ASSIGNABLE_PERSONS
            )
        else:
            # Asignar al que tenga menos tickets entre los disponibles
            person_id = AssignmentTrackerInterface.get_person_with_least_tickets(
                available_persons
            )
            logger.info(f"✅ Asignando en horario laboral ({current_hour}:{current_minute:02d}). Disponibles: {available_persons}")
        
        return person_id

    def assign_ticket_fairly(self) -> int:
        """Asigna un ticket según el horario de trabajo e incrementa el contador.
        
        Returns:
            int: ID de la persona asignada según el horario
        """
        from app.interface.interfaces import AssignmentTrackerInterface
        
        person_id = self.get_next_assignee()
        AssignmentTrackerInterface.increment_count(person_id)
        logger.info(f"🎫 Ticket asignado a persona ID: {person_id}")
        return person_id

    def check_ticket_status(self)->str:
        """Verifica el estado de los tickets en Splynx y actualiza la base de datos"""

        data = self._check_ticket_bd()

        for ticket_data in data["pending_tickets"]:

            ticket_id = ticket_data.get("Ticket_ID", "")
            ticket = self.splynx.get_ticket_data_status(ticket_id)
            return ticket['status']
        return ""

    @staticmethod
    def _check_ticket_bd() -> dict:
        """
        Consulta los tickets que tienen is_created_splynx en falso o 0

        Returns:
            dict: Diccionario con los tickets pendientes de crear en Splynx y estadísticas
        """
        from app.interface.interfaces import IncidentsInterface

        resultado = {
            "total": 0,
            "pending_tickets": []
        }

        try:
            # Obtener todos los incidentes de la base de datos
            incidents = IncidentsInterface.get_all()

            # Filtrar solo los que tienen is_created_splynx en falso o 0
            pending_tickets = []
            for inc in incidents:
                if not inc.is_created_splynx:
                    # Convertir el objeto a diccionario
                    inc_dict = {
                        "id": inc.id,
                        "Cliente": inc.Cliente,
                        "Cliente_Nombre": inc.Cliente_Nombre if hasattr(inc, "Cliente_Nombre") else "",
                        "Asunto": inc.Asunto,
                        "Fecha_Creacion": inc.Fecha_Creacion,
                        "Estado": inc.Estado if hasattr(inc, "Estado") else "",
                        "Prioridad": inc.Prioridad if hasattr(inc, "Prioridad") else "medium",
                        "Ticket_ID": inc.Ticket_ID if hasattr(inc, "Ticket_ID") else "",
                        "is_created_splynx": inc.is_created_splynx
                    }
                    pending_tickets.append(inc_dict)

            # Guardar en el resultado
            resultado["total"] = len(pending_tickets)
            resultado["pending_tickets"] = pending_tickets

            logger.info(f"Se encontraron {resultado['total']} tickets pendientes de crear en Splynx")

        except Exception as e:
            logger.error(f"Error al consultar tickets pendientes: {str(e)}")

        return resultado

    @staticmethod
    def _update_ticket_id_in_db( customer_id: str, subject: str, fecha_creacion: str, ticket_id: str):
        """Actualiza el ID del ticket en la base de datos para el incidente correspondiente.
        
        Args:
            customer_id: ID del cliente
            subject: Asunto del ticket
            fecha_creacion: Fecha de creación
            ticket_id: ID del ticket a actualizar
        
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        from app.interface.interfaces import IncidentsInterface
        
        try:
            # Buscar el incidente por cliente, asunto y fecha
            incidents = IncidentsInterface.get_all()
            target_incident = None
            
            for incident in incidents:
                if (incident.Cliente == customer_id and 
                    incident.Asunto == subject and 
                    incident.Fecha_Creacion == fecha_creacion):
                    target_incident = incident
                    break
            
            if target_incident:
                # Actualizar el incidente
                update_data = {
                    "Ticket_ID": ticket_id,
                    "Estado": "SUCCESS"
                }
                
                updated = IncidentsInterface.update(target_incident.id, update_data)
                if updated:
                    logger.info(f"Ticket ID actualizado en la base de datos: {ticket_id} para {customer_id}")
                    return True
                else:
                    logger.error(f"Error al actualizar Ticket ID en la base de datos para {customer_id}")
                    return False
            else:
                # Si no se encontró un incidente para actualizar, crear uno nuevo
                from datetime import datetime
                
                incident_data = {
                    "Cliente": customer_id,
                    "Asunto": subject,
                    "Fecha_Creacion": fecha_creacion,
                    "Ticket_ID": ticket_id,
                    "Estado": "SUCCESS",
                    "Prioridad": "medium",  # Valor por defecto
                    "is_created_splynx": True
                }
                
                new_incident = IncidentsInterface.create(incident_data)
                if new_incident:
                    logger.info(f"Nuevo ticket creado en la base de datos: {ticket_id} para {customer_id}")
                    return True
                else:
                    logger.error(f"Error al crear nuevo ticket en la base de datos para {customer_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Error al actualizar Ticket ID en la base de datos: {e}")
            return False

    def create_ticket(self):
        """Crea un ticket en Splynx y actualiza la base de datos con el ID devuelto

        Returns:
            list: Lista de IDs de tickets creados o lista vacía si hubo error
        """
        data = self._check_ticket_bd()
        created_tickets = []  # Lista para almacenar los IDs de tickets creados

        for ticket_data in data["pending_tickets"]:
            cliente = ticket_data.get("Cliente", "")
            cliente_nombre = ticket_data.get("Cliente_Nombre", "")  # Obtener nombre desde la BD
            asunto_original = ticket_data.get("Asunto", "")  # Guardar asunto original para búsquedas en BD
            fecha_creacion = ticket_data.get("Fecha_Creacion", "")

            assigned_person_id = self.assign_ticket_fairly()
            
            # Usar el nombre del cliente desde la base de datos
            customer_name = cliente_nombre if cliente_nombre else "Cliente"
            logger.info(f"✅ Nombre del cliente: {customer_name}")
            
            # Agregar prefijo 'GR' a tickets que vienen de Gestion Real (solo para Splynx)
            asunto_splynx = asunto_original
            if asunto_original.startswith("Ticket-"):
                asunto_splynx = f"GR {asunto_original}"
            
            ticket_data = {
                "Cliente": cliente,
                "Asunto": asunto_splynx,  # Usar asunto con prefijo para Splynx
                "Asunto_Original": asunto_original,  # Guardar original para búsquedas en BD
                "note": f"Ticket creado automaticamente por Api Splynx para el cliente {customer_name}, con fecha original de {fecha_creacion}",
                "Fecha_Creacion": fecha_creacion,
                "Prioridad": ticket_data.get("Prioridad", "medium"),
                "assigned_to": assigned_person_id
            }

            # Crear el ticket en Splynx y obtener la respuesta (que incluye el ID)
            response = self.splynx.create_ticket(
                customer_id=ticket_data["Cliente"],
                subject=ticket_data["Asunto"],
                note=ticket_data["note"],
                fecha_creacion=ticket_data["Fecha_Creacion"],
                priority=ticket_data["Prioridad"],
                assigned_to=assigned_person_id
            )

            # Verificar si se creó correctamente y obtener el ID
            if response and isinstance(response, dict) and 'id' in response:
                ticket_id = str(response['id'])
                created_tickets.append(ticket_id)  # Agregar el ID a la lista de tickets creados

                # Actualizar el registro en la base de datos (usar asunto original)
                self._update_ticket_id_in_db(
                    customer_id=ticket_data["Cliente"],
                    subject=ticket_data["Asunto_Original"],
                    fecha_creacion=ticket_data["Fecha_Creacion"],
                    ticket_id=ticket_id
                )
                
                # Registrar asignación en historial
                TicketResponseMetricsInterface.add_assignment_to_history(
                    ticket_id=ticket_id,
                    assigned_to=assigned_person_id,
                    reason="auto_assignment_on_creation"
                )
                
                # Enviar notificación por WhatsApp (si está habilitado)
                from app.utils.constants import WHATSAPP_ENABLED
                if WHATSAPP_ENABLED:
                    from app.services.whatsapp_service import WhatsAppService
                    whatsapp_service = WhatsAppService()
                    
                    notif_resultado = whatsapp_service.send_ticket_assignment_notification(
                        person_id=assigned_person_id,
                        ticket_id=ticket_id,
                        subject=ticket_data["Asunto"],
                        customer_name=customer_name,
                        priority=ticket_data["Prioridad"]
                    )
                    
                    if notif_resultado["success"]:
                        logger.info(f"✅ Notificación enviada a {notif_resultado['operator_name']} para ticket {ticket_id}")
                    else:
                        logger.error(f"❌ Error enviando notificación: {notif_resultado.get('error', 'Unknown')}")
                
                # Actualizar assigned_to en la base de datos (usar asunto original)
                from app.interface.interfaces import IncidentsInterface
                try:
                    incidents = IncidentsInterface.get_all()
                    for incident in incidents:
                        if (incident.Cliente == cliente and
                                incident.Asunto == asunto_original and
                                incident.Fecha_Creacion == fecha_creacion):
                            update_data = {"assigned_to": assigned_person_id}
                            IncidentsInterface.update(incident.id, update_data)
                            logger.info(f"Actualizado assigned_to={assigned_person_id} para ticket {ticket_id}")
                            break
                except Exception as e:
                    logger.error(f"Error al actualizar assigned_to: {e}")

                # Actualizar el estado is_created_splynx a True (usar asunto original)
                try:
                    incidents = IncidentsInterface.get_all()
                    for incident in incidents:
                        if (incident.Cliente == cliente and
                                incident.Asunto == asunto_original and
                                incident.Fecha_Creacion == fecha_creacion):
                            update_data = {"is_created_splynx": True}
                            IncidentsInterface.update(incident.id, update_data)
                            logger.info(f"Actualizado is_created_splynx=True para ticket {ticket_id}")
                            break
                except Exception as e:
                    logger.error(f"Error al actualizar is_created_splynx: {e}")

        # Retornar la lista de tickets creados al final de la función
        return created_tickets if created_tickets else None

    def check_and_alert_overdue_tickets(self, threshold_minutes=45):
        """Verifica tickets asignados que superen el tiempo límite y envía alertas por WhatsApp
        Agrupa todos los tickets vencidos por operador y envía un solo mensaje con la lista completa
        
        Lógica:
        - Solo alerta si el ticket tiene más de 45 minutos desde creación
        - NO alerta si el ticket fue actualizado hace menos de 30 minutos
        - Registra métricas en la base de datos
        - Usa nombres de operadores en los mensajes
        
        Args:
            threshold_minutes: Tiempo límite en minutos (default 45)
            
        Returns:
            dict: Resumen de la operación con estadísticas
        """
        from app.utils.constants import (
            TICKET_UPDATE_THRESHOLD_MINUTES,
            TICKET_RENOTIFICATION_INTERVAL_MINUTES,
            SPLYNX_SUPPORT_GROUP_ID,
            TIMEZONE
        )
        from app.services.whatsapp_service import WhatsAppService
        from app.interface.interfaces import TicketResponseMetricsInterface
        from datetime import datetime, timedelta
        from collections import defaultdict
        import pytz
        
        resultado = {
            "total_tickets_revisados": 0,
            "tickets_vencidos": 0,
            "alertas_enviadas": 0,
            "errores": 0,
            "detalles": []
        }
        
        try:
            # Inicializar servicio de WhatsApp
            whatsapp_service = WhatsAppService()
            
            # Obtener todos los tickets asignados del grupo de Soporte Técnico
            tickets = self.splynx.get_assigned_tickets(group_id=SPLYNX_SUPPORT_GROUP_ID)
            resultado["total_tickets_revisados"] = len(tickets)
            
            if not tickets:
                logger.info("No hay tickets asignados para revisar")
                return resultado
            
            logger.info("="*60)
            logger.info(f"🔍 REVISANDO {len(tickets)} TICKETS ASIGNADOS")
            logger.info(f"⏱️  Umbral de alerta: {threshold_minutes} minutos")
            logger.info("="*60)
            
            # Obtener hora actual en Argentina
            tz_argentina = pytz.timezone(TIMEZONE)
            now = datetime.now(tz_argentina)
            
            # Diccionario para agrupar tickets por operador
            tickets_por_operador = defaultdict(list)
            
            for ticket in tickets:
                ticket_id = ticket.get('id')
                subject = ticket.get('subject', 'Sin asunto')
                customer_id = ticket.get('customer_id', 'N/A')
                assigned_to = int(ticket.get('assign_to', 0))
                created_at_str = ticket.get('created_at', '')
                updated_at_str = ticket.get('updated_at', '')
                status_id = str(ticket.get('status_id', ''))
                
                try:
                    # Parsear fecha de creación del ticket
                    # Formato esperado: "YYYY-MM-DD HH:MM:SS"
                    created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                    created_at = tz_argentina.localize(created_at)
                    
                    # Parsear fecha de última actualización
                    if updated_at_str:
                        try:
                            updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                            updated_at = tz_argentina.localize(updated_at)
                        except ValueError:
                            # Si hay error parseando updated_at, usar now
                            logger.warning(f"⚠️  Error parseando updated_at para ticket {ticket_id}, usando now")
                            updated_at = now
                    else:
                        # Si no hay updated_at, usar now
                        updated_at = now
                    
                    # Calcular tiempo transcurrido desde creación hasta última actualización
                    time_elapsed = updated_at - created_at
                    minutes_elapsed = int(time_elapsed.total_seconds() / 60)
                    
                    # Calcular tiempo desde última actualización hasta ahora
                    time_since_update = now - updated_at
                    minutes_since_update = int(time_since_update.total_seconds() / 60)
                    
                    # Verificar si el ticket está en estado OutHouse (ID 6)
                    from app.utils.constants import OUTHOUSE_STATUS_ID, OUTHOUSE_NO_ALERT_MINUTES
                    if status_id == OUTHOUSE_STATUS_ID:
                        if minutes_since_update < OUTHOUSE_NO_ALERT_MINUTES:
                            logger.info(f"🏠 Ticket {ticket_id} en estado OutHouse - No se alerta hasta 2 horas ({minutes_since_update} min transcurridos)")
                            continue
                    
                    # Verificar si supera el umbral de 45 minutos desde creación hasta última actualización
                    if minutes_elapsed >= threshold_minutes:
                        
                        # Si fue actualizado hace menos de 45 minutos, NO alertar
                        should_alert = True
                        if minutes_since_update < TICKET_UPDATE_THRESHOLD_MINUTES:
                            should_alert = False
                            logger.info(f"⏭️  Ticket {ticket_id} actualizado hace {minutes_since_update} min - NO se alerta")
                        
                        if not should_alert:
                            continue
                        resultado["tickets_vencidos"] += 1
                        
                        # Verificar si ya fue notificado recientemente (ANTI-SPAM)
                        existing_metric = TicketResponseMetricsInterface.get_by_ticket_id(str(ticket_id))
                        should_notify = True
                        
                        if existing_metric and existing_metric.last_alert_sent_at:
                            # Calcular tiempo desde última notificación
                            last_alert = existing_metric.last_alert_sent_at
                            if last_alert.tzinfo is None:
                                last_alert = tz_argentina.localize(last_alert)
                            else:
                                # Convertir a timezone de Argentina si tiene otro timezone
                                last_alert = last_alert.astimezone(tz_argentina)
                            
                            minutes_since_last_alert = (now - last_alert).total_seconds() / 60
                            
                            # Si el tiempo es negativo, significa que hay un problema de timezone - alertar de todos modos
                            if minutes_since_last_alert < 0:
                                logger.warning(f"⚠️  Ticket {ticket_id} tiene last_alert en el futuro ({int(minutes_since_last_alert)} min) - forzando alerta")
                                should_notify = True
                            elif minutes_since_last_alert < TICKET_RENOTIFICATION_INTERVAL_MINUTES:
                                should_notify = False
                                logger.info(f"⏭️  Ticket {ticket_id} ya fue notificado hace {int(minutes_since_last_alert)} min - omitiendo")
                                resultado["detalles"].append({
                                    "ticket_id": ticket_id,
                                    "subject": subject,
                                    "assigned_to": assigned_to,
                                    "minutes_elapsed": minutes_elapsed,
                                    "estado": "YA_NOTIFICADO_RECIENTEMENTE",
                                    "minutes_since_last_alert": int(minutes_since_last_alert)
                                })
                                continue
                        
                        if not should_notify:
                            continue
                        
                        # Obtener información del cliente
                        customer_info = self.splynx.search_customer(str(customer_id))
                        customer_name = customer_info.get('name', 'Cliente desconocido') if customer_info else 'Cliente desconocido'
                        
                        # Obtener nombre del operador
                        operator_name = whatsapp_service.get_operator_name(assigned_to)
                        
                        # Preparar datos del ticket
                        ticket_data = {
                            'id': ticket_id,
                            'subject': subject,
                            'customer_name': customer_name,
                            'created_at': created_at_str,
                            'minutes_elapsed': minutes_elapsed,
                            'operator_name': operator_name
                        }
                        
                        # Registrar o actualizar métrica en la base de datos
                        if not existing_metric:
                            # Crear nueva métrica (se actualizará last_alert_sent_at al enviar)
                            metric_data = {
                                'ticket_id': str(ticket_id),
                                'assigned_to': assigned_to,
                                'customer_id': str(customer_id),
                                'customer_name': customer_name,
                                'subject': subject,
                                'created_at': created_at,
                                'first_alert_sent_at': None,  # Se actualizará al enviar
                                'last_alert_sent_at': None,   # Se actualizará al enviar
                                'response_time_minutes': minutes_elapsed,
                                'alert_count': 0,  # Se incrementará al enviar
                                'exceeded_threshold': True
                            }
                            TicketResponseMetricsInterface.create(metric_data)
                            logger.info(f"📊 Métrica creada para ticket {ticket_id}")
                        
                        # Agrupar por operador (se actualizará métrica después de enviar)
                        if whatsapp_service.get_operator_phone(assigned_to):
                            tickets_por_operador[assigned_to].append(ticket_data)
                            logger.info(f"📋 Ticket {ticket_id} agregado a lista de {operator_name} - {minutes_elapsed} min")
                        else:
                            logger.warning(f"⚠️  {operator_name} no tiene número de WhatsApp configurado")
                            resultado["detalles"].append({
                                "ticket_id": ticket_id,
                                "subject": subject,
                                "assigned_to": assigned_to,
                                "minutes_elapsed": minutes_elapsed,
                                "estado": "SIN_NUMERO_WHATSAPP"
                            })
                    
                except ValueError as e:
                    logger.warning(f"⚠️  Error parseando fecha del ticket {ticket_id}: {e}")
                    resultado["errores"] += 1
                except Exception as e:
                    logger.error(f"❌ Error procesando ticket {ticket_id}: {e}")
                    resultado["errores"] += 1
            
            # Enviar alertas agrupadas por operador (si WhatsApp está habilitado)
            from app.utils.constants import WHATSAPP_ENABLED
            
            if WHATSAPP_ENABLED:
                logger.info("="*60)
                logger.info(f"📤 ENVIANDO ALERTAS AGRUPADAS")
                logger.info("="*60)
                
                for assigned_to, tickets_list in tickets_por_operador.items():
                    # Usar WhatsAppService para enviar alertas
                    envio_resultado = whatsapp_service.send_overdue_tickets_alert(assigned_to, tickets_list)
                    
                    if envio_resultado["success"]:
                        resultado["alertas_enviadas"] += 1
                        
                        # Actualizar métricas de todos los tickets enviados
                        for ticket_data in tickets_list:
                            ticket_id = str(ticket_data['id'])
                            minutes_elapsed = ticket_data['minutes_elapsed']
                            
                            # Actualizar last_alert_sent_at y alert_count (crea métrica si no existe)
                            update_success = TicketResponseMetricsInterface.update_alert_sent(
                                ticket_id=ticket_id,
                                response_time_minutes=minutes_elapsed,
                                assigned_to=assigned_to,
                                customer_id=ticket_data.get('customer_id'),
                                customer_name=ticket_data.get('customer_name'),
                                subject=ticket_data.get('subject'),
                                created_at=None  # Se usará datetime.now() si no existe
                            )
                            
                            if update_success:
                                logger.info(f"   ✅ Ticket {ticket_id}: last_alert_sent_at actualizado")
                            else:
                                logger.error(f"   ❌ Ticket {ticket_id}: ERROR al actualizar last_alert_sent_at")
                            
                            resultado["detalles"].append({
                                "ticket_id": ticket_id,
                                "subject": ticket_data['subject'],
                                "assigned_to": assigned_to,
                                "minutes_elapsed": minutes_elapsed,
                                "phone": envio_resultado["phone_number"],
                                "estado": "ALERTA_ENVIADA"
                            })
                        
                        logger.info(f"✅ Métricas actualizadas para {len(tickets_list)} tickets")
                    else:
                        resultado["errores"] += 1
                        
                        # Marcar todos los tickets como error
                        for ticket_data in tickets_list:
                            resultado["detalles"].append({
                                "ticket_id": ticket_data['id'],
                                "subject": ticket_data['subject'],
                                "assigned_to": assigned_to,
                                "minutes_elapsed": ticket_data['minutes_elapsed'],
                                "estado": "ERROR_ENVIO",
                                "error": envio_resultado.get("error")
                            })
            else:
                logger.info(f"ℹ️  WhatsApp deshabilitado - no se enviaron alertas de tickets vencidos")
                logger.info(f"   Se encontraron {len(tickets_por_operador)} operadores con tickets vencidos")
            
            logger.info("="*60)
            logger.info(f"✅ REVISIÓN COMPLETADA")
            logger.info(f"   Total revisados: {resultado['total_tickets_revisados']}")
            logger.info(f"   Tickets vencidos: {resultado['tickets_vencidos']}")
            logger.info(f"   Operadores alertados: {resultado['alertas_enviadas']}")
            logger.info(f"   Errores: {resultado['errores']}")
            logger.info("="*60)
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error general en revisión de tickets: {e}")
            resultado["errores"] = resultado["total_tickets_revisados"]
            return resultado

    def send_end_of_shift_notifications(self):
        """Envía notificaciones de resumen 1 hora antes del fin de turno
        
        Verifica si algún operador está a 1 hora de terminar su turno y le envía
        un resumen con todos sus tickets pendientes.
        
        Solo se ejecuta de lunes a viernes.
        
        Returns:
            dict: Resumen de la operación con estadísticas
        """
        from app.utils.constants import (
            OPERATOR_SCHEDULES,
            END_OF_SHIFT_NOTIFICATION_MINUTES,
            SPLYNX_SUPPORT_GROUP_ID,
            TIMEZONE
        )
        from app.services.whatsapp_service import WhatsAppService
        from datetime import datetime, timedelta
        import pytz
        
        resultado = {
            "operadores_notificados": 0,
            "total_tickets_reportados": 0,
            "errores": 0,
            "detalles": []
        }
        
        try:
            # Obtener hora actual en Argentina
            tz_argentina = pytz.timezone(TIMEZONE)
            now = datetime.now(tz_argentina)
            
            # Verificar si es día laboral (lunes a viernes)
            if now.weekday() >= 5:  # 5 = sábado, 6 = domingo
                logger.info(f"⏭️  Hoy es {['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'][now.weekday()]} - No se envían notificaciones de fin de turno")
                return resultado
            
            current_time = now.strftime("%H:%M")
            current_hour = now.hour
            current_minute = now.minute
            
            logger.info("="*60)
            logger.info(f"🕐 VERIFICANDO NOTIFICACIONES DE FIN DE TURNO")
            logger.info(f"⏰ Hora actual: {current_time}")
            logger.info("="*60)
            
            # Inicializar servicio de WhatsApp
            whatsapp_service = WhatsAppService()
            
            # Verificar cada operador
            for person_id, schedules in OPERATOR_SCHEDULES.items():
                operator_name = whatsapp_service.get_operator_name(person_id)
                
                # Verificar cada turno del operador
                for schedule in schedules:
                    start_time_str = schedule["start"]
                    end_time_str = schedule["end"]
                    start_hour, start_minute = map(int, start_time_str.split(":"))
                    end_hour, end_minute = map(int, end_time_str.split(":"))
                    
                    # Excluir turno nocturno (00:00-08:00)
                    if start_time_str == "00:00" and end_time_str == "08:00":
                        logger.info(f"   {operator_name}: Turno nocturno {start_time_str}-{end_time_str} - OMITIDO (sin notificación)")
                        continue
                    
                    # Convertir a minutos desde medianoche para comparación
                    start_minutes = start_hour * 60 + start_minute
                    end_minutes = end_hour * 60 + end_minute
                    current_minutes = current_hour * 60 + current_minute
                    
                    # Verificar si el operador está actualmente en su turno
                    is_in_shift = False
                    if start_minutes < end_minutes:
                        # Turno normal (ej: 08:00 - 16:00)
                        is_in_shift = start_minutes <= current_minutes < end_minutes
                    else:
                        # Turno que cruza medianoche (ej: 23:00 - 02:00)
                        is_in_shift = current_minutes >= start_minutes or current_minutes < end_minutes
                    
                    # Calcular la hora de notificación (1 hora antes del fin)
                    notification_time = datetime(now.year, now.month, now.day, end_hour, end_minute) - timedelta(minutes=END_OF_SHIFT_NOTIFICATION_MINUTES)
                    notification_hour = notification_time.hour
                    notification_minute = notification_time.minute
                    notification_minutes = notification_hour * 60 + notification_minute
                    
                    # Debug: mostrar cálculos
                    logger.debug(f"   {operator_name}: Turno {start_time_str}-{end_time_str}, notificar a las {notification_hour:02d}:{notification_minute:02d}")
                    logger.debug(f"   En turno: {is_in_shift}, Hora actual: {current_hour:02d}:{current_minute:02d}")
                    
                    # Verificar si es el momento exacto de enviar la notificación (con margen de ±2 minutos)
                    time_diff = abs(current_minutes - notification_minutes)
                    
                    logger.debug(f"   Diferencia: {time_diff} minutos")
                    
                    # IMPORTANTE: Solo notificar si está en turno Y es el momento correcto
                    if is_in_shift and time_diff <= 2:  # Margen de 2 minutos
                        logger.info(f"🔔 Es momento de notificar a {operator_name} (turno termina a las {end_time_str})")
                        
                        # Obtener todos los tickets asignados a este operador
                        all_tickets = self.splynx.get_assigned_tickets(group_id=SPLYNX_SUPPORT_GROUP_ID)
                        operator_tickets = [
                            ticket for ticket in all_tickets 
                            if int(ticket.get('assign_to', 0)) == person_id
                        ]
                        
                        logger.info(f"📋 {operator_name} tiene {len(operator_tickets)} ticket(s) asignado(s)")
                        
                        # Preparar datos de tickets para el mensaje
                        tickets_data = []
                        for ticket in operator_tickets:
                            customer_id = ticket.get('customer_id', 'N/A')
                            customer_info = self.splynx.search_customer(str(customer_id))
                            customer_name = customer_info.get('name', 'Cliente desconocido') if customer_info else 'Cliente desconocido'
                            
                            tickets_data.append({
                                'id': ticket.get('id'),
                                'subject': ticket.get('subject', 'Sin asunto'),
                                'customer_name': customer_name,
                                'status': ticket.get('status', 'Abierto')
                            })
                        
                        # Enviar notificación usando WhatsAppService
                        envio_resultado = whatsapp_service.send_end_of_shift_summary(
                            person_id=person_id,
                            tickets_list=tickets_data,
                            shift_end_time=end_time_str
                        )
                        
                        if envio_resultado["success"]:
                            resultado["operadores_notificados"] += 1
                            resultado["total_tickets_reportados"] += len(tickets_data)
                            resultado["detalles"].append({
                                "operador": operator_name,
                                "person_id": person_id,
                                "turno_termina": end_time_str,
                                "tickets_pendientes": len(tickets_data),
                                "estado": "NOTIFICACION_ENVIADA"
                            })
                        else:
                            resultado["errores"] += 1
                            resultado["detalles"].append({
                                "operador": operator_name,
                                "person_id": person_id,
                                "estado": "ERROR_ENVIO",
                                "error": envio_resultado.get("error")
                            })
            
            logger.info("="*60)
            logger.info(f"✅ VERIFICACIÓN COMPLETADA")
            logger.info(f"   Operadores notificados: {resultado['operadores_notificados']}")
            logger.info(f"   Total tickets reportados: {resultado['total_tickets_reportados']}")
            logger.info(f"   Errores: {resultado['errores']}")
            logger.info("="*60)
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error general en notificaciones de fin de turno: {e}")
            resultado["errores"] += 1
            return resultado

    def assign_unassigned_tickets(self, group_id="4"):
        """Asigna tickets no asignados del grupo de Soporte Técnico usando round-robin
        
        Args:
            group_id: ID del grupo (default "4" para Soporte Técnico)
            
        Returns:
            dict: Resumen de la operación con estadísticas
        """
        # Verificar si el sistema está pausado
        from app.utils.system_control import SystemControl
        
        if SystemControl.is_paused():
            logger.warning("⏸️  Sistema PAUSADO - No se asignarán tickets")
            return {
                "total_tickets": 0,
                "asignados_exitosamente": 0,
                "errores": 0,
                "detalles": [],
                "system_paused": True,
                "message": "Sistema pausado - asignación deshabilitada"
            }
        
        resultado = {
            "total_tickets": 0,
            "asignados_exitosamente": 0,
            "errores": 0,
            "detalles": []
        }
        
        try:
            # Obtener tickets no asignados del grupo
            tickets = self.splynx.get_unassigned_tickets(group_id)
            resultado["total_tickets"] = len(tickets)
            
            if not tickets:
                logger.info("No hay tickets sin asignar")
                return resultado
            
            logger.info("="*60)
            logger.info(f"🎫 ASIGNANDO {len(tickets)} TICKETS NO ASIGNADOS")
            logger.info("="*60)
            
            for ticket in tickets:
                ticket_id = ticket.get('id')
                subject = ticket.get('subject', 'Sin asunto')
                customer_id = ticket.get('customer_id', 'N/A')
                note = ticket.get('note', '')  # Obtener la nota del ticket
                
                try:
                    from app.interface.interfaces import AssignmentTrackerInterface
                    
                    # Obtener la siguiente persona a asignar SIN incrementar el contador
                    # Pasar la nota para verificar etiquetas [TT] o [TD]
                    assigned_person_id = self.get_next_assignee(ticket_note=note)
                    
                    # Actualizar el ticket en Splynx
                    response = self.splynx.update_ticket_assignment(ticket_id, assigned_person_id)
                    
                    if response:
                        # Solo incrementar el contador si la asignación fue exitosa
                        AssignmentTrackerInterface.increment_count(assigned_person_id)
                        
                        # Registrar asignación en historial
                        TicketResponseMetricsInterface.add_assignment_to_history(
                            ticket_id=str(ticket_id),
                            assigned_to=assigned_person_id,
                            reason="auto_assignment"
                        )
                        
                        # Enviar notificación por WhatsApp (si está habilitado)
                        from app.utils.constants import WHATSAPP_ENABLED
                        notificacion_enviada = False
                        
                        if WHATSAPP_ENABLED:
                            # Obtener información del cliente para la notificación
                            customer_info = self.splynx.search_customer(str(customer_id))
                            customer_name = customer_info.get('name', 'Cliente desconocido') if customer_info else 'Cliente desconocido'
                            
                            # Obtener prioridad del ticket
                            priority = ticket.get('priority', 'medium')
                            
                            from app.services.whatsapp_service import WhatsAppService
                            whatsapp_service = WhatsAppService()
                            
                            notif_resultado = whatsapp_service.send_ticket_assignment_notification(
                                person_id=assigned_person_id,
                                ticket_id=str(ticket_id),
                                subject=subject,
                                customer_name=customer_name,
                                priority=priority
                            )
                            notificacion_enviada = notif_resultado["success"]
                        else:
                            logger.info(f"ℹ️  WhatsApp deshabilitado - no se envió notificación para ticket {ticket_id}")
                        
                        resultado["asignados_exitosamente"] += 1
                        resultado["detalles"].append({
                            "ticket_id": ticket_id,
                            "subject": subject,
                            "customer_id": customer_id,
                            "assigned_to": assigned_person_id,
                            "notificacion_enviada": notificacion_enviada,
                            "estado": "ASIGNADO"
                        })
                        logger.info(f"✅ Ticket {ticket_id} asignado a persona {assigned_person_id}")
                    else:
                        resultado["errores"] += 1
                        resultado["detalles"].append({
                            "ticket_id": ticket_id,
                            "subject": subject,
                            "estado": "ERROR",
                            "error": "No se pudo actualizar en Splynx"
                        })
                        logger.error(f"❌ Error asignando ticket {ticket_id}")
                        
                except Exception as e:
                    resultado["errores"] += 1
                    resultado["detalles"].append({
                        "ticket_id": ticket_id,
                        "subject": subject,
                        "estado": "ERROR",
                        "error": str(e)
                    })
                    logger.error(f"❌ Error procesando ticket {ticket_id}: {e}")
            
            logger.info("="*60)
            logger.info(f"✅ ASIGNACIÓN COMPLETADA")
            logger.info(f"   Total: {resultado['total_tickets']}")
            logger.info(f"   Asignados: {resultado['asignados_exitosamente']}")
            logger.info(f"   Errores: {resultado['errores']}")
            logger.info("="*60)
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error general en asignación de tickets: {e}")
            resultado["errores"] = resultado["total_tickets"]
            return resultado
    
    def auto_unassign_after_shift(self):
        """Desasigna tickets automáticamente 1 hora después del fin de turno del operador"""
        from app.utils.constants import OPERATOR_SCHEDULES
        import pytz
        from datetime import datetime
        
        resultado = {
            "tickets_revisados": 0,
            "tickets_desasignados": 0,
            "errores": 0,
            "detalles": []
        }
        
        try:
            # Obtener hora actual en Argentina
            tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz_argentina)
            current_time_minutes = now.hour * 60 + now.minute
            
            logger.info("="*60)
            logger.info(f"🔄 VERIFICANDO DESASIGNACIÓN AUTOMÁTICA")
            logger.info(f"⏰ Hora actual: {now.strftime('%H:%M')}")
            logger.info("="*60)
            
            # Obtener todos los tickets asignados (status != 3 = no cerrados)
            tickets = self.splynx.get_assigned_tickets()
            
            if not tickets:
                logger.info("ℹ️  No hay tickets asignados para revisar")
                return resultado
            
            resultado["tickets_revisados"] = len(tickets)
            logger.info(f"📋 Revisando {len(tickets)} tickets asignados")
            
            for ticket in tickets:
                ticket_id = ticket.get('id')
                assigned_to = ticket.get('assigned_to')
                subject = ticket.get('subject', 'Sin asunto')
                
                # Verificar si el operador tiene horarios definidos
                if assigned_to not in OPERATOR_SCHEDULES:
                    continue
                
                schedules = OPERATOR_SCHEDULES[assigned_to]
                operator_name = self.get_operator_name(assigned_to)
                
                # Verificar si pasaron 30 minutos desde el fin de algún turno
                should_unassign = False
                shift_end_time = None
                
                for schedule in schedules:
                    end_minutes = schedule["end_hour"] * 60 + schedule["end_minute"]
                    minutes_after_shift = current_time_minutes - end_minutes
                    
                    # Si pasaron entre 60 y 90 minutos del fin de turno (1 hora después)
                    if 60 <= minutes_after_shift <= 90:
                        should_unassign = True
                        shift_end_time = f"{schedule['end_hour']:02d}:{schedule['end_minute']:02d}"
                        logger.info(f"⏰ Operador {operator_name} (ID {assigned_to}): Turno terminó a las {shift_end_time}")
                        logger.info(f"   Han pasado {minutes_after_shift} minutos desde el fin de turno")
                        break
                
                if should_unassign:
                    # Desasignar ticket (assigned_to = 0 o NULL)
                    response = self.splynx.update_ticket_assignment(ticket_id, 0)
                    
                    if response:
                        resultado["tickets_desasignados"] += 1
                        
                        # Registrar desasignación en historial
                        TicketResponseMetricsInterface.add_assignment_to_history(
                            ticket_id=str(ticket_id),
                            assigned_to=0,
                            reason=f"auto_unassign_after_shift_end_{shift_end_time}"
                        )
                        
                        logger.info(f"   ✅ Ticket {ticket_id} desasignado de {operator_name}")
                        
                        resultado["detalles"].append({
                            "ticket_id": ticket_id,
                            "subject": subject,
                            "previous_assigned_to": assigned_to,
                            "operator_name": operator_name,
                            "shift_end_time": shift_end_time,
                            "estado": "DESASIGNADO"
                        })
                    else:
                        resultado["errores"] += 1
                        logger.error(f"   ❌ Error al desasignar ticket {ticket_id}")
            
            logger.info("="*60)
            logger.info(f"✅ DESASIGNACIÓN AUTOMÁTICA COMPLETADA")
            logger.info(f"   Tickets revisados: {resultado['tickets_revisados']}")
            logger.info(f"   Tickets desasignados: {resultado['tickets_desasignados']}")
            logger.info(f"   Errores: {resultado['errores']}")
            logger.info("="*60)
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error en desasignación automática: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return resultado
    
    def get_operator_name(self, person_id: int) -> str:
        """Obtiene el nombre del operador por su ID"""
        from app.utils.constants import PERSON_NAMES
        return PERSON_NAMES.get(person_id, f"Operador {person_id}")
