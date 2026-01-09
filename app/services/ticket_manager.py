"""
Ticket Manager - Handles ticket filtering and cleanup operations
Separates business logic from API calls
"""


from app.services.splynx_services import SplynxServices
from datetime import datetime
import pytz


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

    def get_next_assignee(self) -> int:
        """Obtiene la siguiente persona a asignar según horario y round-robin, SIN incrementar contador.
        
        Turnos:
        - ID 10 y 37: 12:00 AM - 8:00 AM (turno nocturno)
        - ID 37: 8:00 AM - 3:00 PM
        - ID 10: 8:00 AM - 4:00 PM
        - ID 27: 10:00 AM - 5:20 PM
        - ID 38: 5:00 PM - 11:00 PM
        
        Returns:
            int: ID de la persona a asignar según el horario
        """
        from app.interface.interfaces import AssignmentTrackerInterface
        
        # Obtener hora actual en Argentina
        tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
        now = datetime.now(tz_argentina)
        current_hour = now.hour
        current_minute = now.minute
        current_time_minutes = current_hour * 60 + current_minute
        
        # Definir horarios en minutos desde medianoche
        # Turno nocturno: 12:00 AM (0) - 8:00 AM (480) -> IDs 10 y 37
        # ID 37: 8:00 AM (480) - 3:00 PM (900)
        # ID 10: 8:00 AM (480) - 4:00 PM (960)
        # ID 27: 10:00 AM (600) - 5:20 PM (1040)
        # ID 38: 5:00 PM (1020) - 11:00 PM (1380)
        
        available_persons = []
        
        # Turno nocturno: 12:00 AM - 8:00 AM
        if 0 <= current_time_minutes < 480:
            available_persons.extend([10, 37])
        
        # Verificar quién está disponible según el horario diurno
        if 480 <= current_time_minutes < 900:  # 8:00 AM - 3:00 PM
            available_persons.append(37)
        
        if 480 <= current_time_minutes < 960:  # 8:00 AM - 4:00 PM
            available_persons.append(10)
        
        if 600 <= current_time_minutes < 1040:  # 10:00 AM - 5:20 PM
            available_persons.append(27)
        
        if 1020 <= current_time_minutes <= 1380:  # 5:00 PM - 11:00 PM
            available_persons.append(38)
        
        # Si no hay nadie disponible, usar fallback (round-robin entre todos)
        if not available_persons:
            print(f"⚠️  Fuera de horario laboral ({current_hour}:{current_minute:02d}). Usando asignación round-robin.")
            person_id = AssignmentTrackerInterface.get_person_with_least_tickets(
                self.ASSIGNABLE_PERSONS
            )
        else:
            # Asignar al que tenga menos tickets entre los disponibles
            person_id = AssignmentTrackerInterface.get_person_with_least_tickets(
                available_persons
            )
            print(f"✅ Asignando en horario laboral ({current_hour}:{current_minute:02d}). Disponibles: {available_persons}")
        
        return person_id

    def assign_ticket_fairly(self) -> int:
        """Asigna un ticket según el horario de trabajo e incrementa el contador.
        
        Returns:
            int: ID de la persona asignada según el horario
        """
        from app.interface.interfaces import AssignmentTrackerInterface
        
        person_id = self.get_next_assignee()
        AssignmentTrackerInterface.increment_count(person_id)
        print(f"🎫 Ticket asignado a persona ID: {person_id}")
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

            print(f"Se encontraron {resultado['total']} tickets pendientes de crear en Splynx")

        except Exception as e:
            print(f"Error al consultar tickets pendientes: {str(e)}")

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
                    print(f"Ticket ID actualizado en la base de datos: {ticket_id} para {customer_id}")
                    return True
                else:
                    print(f"Error al actualizar Ticket ID en la base de datos para {customer_id}")
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
                    print(f"Nuevo ticket creado en la base de datos: {ticket_id} para {customer_id}")
                    return True
                else:
                    print(f"Error al crear nuevo ticket en la base de datos para {customer_id}")
                    return False
                
        except Exception as e:
            print(f"Error al actualizar Ticket ID en la base de datos: {e}")
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
            asunto = ticket_data.get("Asunto", "")
            fecha_creacion = ticket_data.get("Fecha_Creacion", "")

            assigned_person_id = self.assign_ticket_fairly()
            
            # Usar el nombre del cliente desde la base de datos
            customer_name = cliente_nombre if cliente_nombre else "Cliente"
            print(f"✅ Nombre del cliente: {customer_name}")
            
            ticket_data = {
                "Cliente": cliente,
                "Asunto": asunto,
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

                # Actualizar el registro en la base de datos
                self._update_ticket_id_in_db(
                    customer_id=ticket_data["Cliente"],
                    subject=ticket_data["Asunto"],
                    fecha_creacion=ticket_data["Fecha_Creacion"],
                    ticket_id=ticket_id
                )
                
                # Actualizar assigned_to en la base de datos
                from app.interface.interfaces import IncidentsInterface
                try:
                    incidents = IncidentsInterface.get_all()
                    for incident in incidents:
                        if (incident.Cliente == cliente and
                                incident.Asunto == asunto and
                                incident.Fecha_Creacion == fecha_creacion):
                            update_data = {"assigned_to": assigned_person_id}
                            IncidentsInterface.update(incident.id, update_data)
                            print(f"Actualizado assigned_to={assigned_person_id} para ticket {ticket_id}")
                            break
                except Exception as e:
                    print(f"Error al actualizar assigned_to: {e}")

                # Actualizar el estado is_created_splynx a True
                try:
                    incidents = IncidentsInterface.get_all()
                    for incident in incidents:
                        if (incident.Cliente == cliente and
                                incident.Asunto == asunto and
                                incident.Fecha_Creacion == fecha_creacion):
                            update_data = {"is_created_splynx": True}
                            IncidentsInterface.update(incident.id, update_data)
                            print(f"Actualizado is_created_splynx=True para ticket {ticket_id}")
                            break
                except Exception as e:
                    print(f"Error al actualizar is_created_splynx: {e}")

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
                print("No hay tickets asignados para revisar")
                return resultado
            
            print(f"\n{'='*60}")
            print(f"🔍 REVISANDO {len(tickets)} TICKETS ASIGNADOS")
            print(f"⏱️  Umbral de alerta: {threshold_minutes} minutos")
            print(f"{'='*60}\n")
            
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
                
                try:
                    # Parsear fecha de creación del ticket
                    # Formato esperado: "YYYY-MM-DD HH:MM:SS"
                    created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                    created_at = tz_argentina.localize(created_at)
                    
                    # Calcular tiempo transcurrido desde creación
                    time_elapsed = now - created_at
                    minutes_elapsed = int(time_elapsed.total_seconds() / 60)
                    
                    # Verificar si supera el umbral de 45 minutos desde creación
                    if minutes_elapsed >= threshold_minutes:
                        
                        # Verificar updated_at - si fue actualizado hace menos de 30 minutos, NO alertar
                        should_alert = True
                        if updated_at_str:
                            try:
                                updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                                updated_at = tz_argentina.localize(updated_at)
                                time_since_update = now - updated_at
                                minutes_since_update = int(time_since_update.total_seconds() / 60)
                                
                                if minutes_since_update < TICKET_UPDATE_THRESHOLD_MINUTES:
                                    should_alert = False
                                    print(f"⏭️  Ticket {ticket_id} actualizado hace {minutes_since_update} min - NO se alerta")
                            except ValueError:
                                # Si hay error parseando updated_at, alertar de todas formas
                                print(f"⚠️  Error parseando updated_at para ticket {ticket_id}, se procederá con alerta")
                        
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
                            
                            minutes_since_last_alert = (now - last_alert).total_seconds() / 60
                            
                            if minutes_since_last_alert < TICKET_RENOTIFICATION_INTERVAL_MINUTES:
                                should_notify = False
                                print(f"⏭️  Ticket {ticket_id} ya fue notificado hace {int(minutes_since_last_alert)} min - omitiendo")
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
                            print(f"📊 Métrica creada para ticket {ticket_id}")
                        
                        # Agrupar por operador (se actualizará métrica después de enviar)
                        if whatsapp_service.get_operator_phone(assigned_to):
                            tickets_por_operador[assigned_to].append(ticket_data)
                            print(f"📋 Ticket {ticket_id} agregado a lista de {operator_name} - {minutes_elapsed} min")
                        else:
                            print(f"⚠️  {operator_name} no tiene número de WhatsApp configurado")
                            resultado["detalles"].append({
                                "ticket_id": ticket_id,
                                "subject": subject,
                                "assigned_to": assigned_to,
                                "minutes_elapsed": minutes_elapsed,
                                "estado": "SIN_NUMERO_WHATSAPP"
                            })
                    
                except ValueError as e:
                    print(f"⚠️  Error parseando fecha del ticket {ticket_id}: {e}")
                    resultado["errores"] += 1
                except Exception as e:
                    print(f"❌ Error procesando ticket {ticket_id}: {e}")
                    resultado["errores"] += 1
            
            # Enviar alertas agrupadas por operador
            print(f"\n{'='*60}")
            print(f"📤 ENVIANDO ALERTAS AGRUPADAS")
            print(f"{'='*60}\n")
            
            for assigned_to, tickets_list in tickets_por_operador.items():
                # Usar WhatsAppService para enviar alertas
                envio_resultado = whatsapp_service.send_overdue_tickets_alert(assigned_to, tickets_list)
                
                if envio_resultado["success"]:
                    resultado["alertas_enviadas"] += 1
                    
                    # Actualizar métricas de todos los tickets enviados
                    for ticket_data in tickets_list:
                        ticket_id = str(ticket_data['id'])
                        minutes_elapsed = ticket_data['minutes_elapsed']
                        
                        # Actualizar last_alert_sent_at y alert_count
                        TicketResponseMetricsInterface.update_alert_sent(ticket_id, minutes_elapsed)
                        
                        resultado["detalles"].append({
                            "ticket_id": ticket_id,
                            "subject": ticket_data['subject'],
                            "assigned_to": assigned_to,
                            "minutes_elapsed": minutes_elapsed,
                            "phone": envio_resultado["phone_number"],
                            "estado": "ALERTA_ENVIADA"
                        })
                    
                    print(f"✅ Métricas actualizadas para {len(tickets_list)} tickets")
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
            
            print(f"\n{'='*60}")
            print(f"✅ REVISIÓN COMPLETADA")
            print(f"   Total revisados: {resultado['total_tickets_revisados']}")
            print(f"   Tickets vencidos: {resultado['tickets_vencidos']}")
            print(f"   Operadores alertados: {resultado['alertas_enviadas']}")
            print(f"   Errores: {resultado['errores']}")
            print(f"{'='*60}\n")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error general en revisión de tickets: {e}")
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
                print(f"⏭️  Hoy es {['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'][now.weekday()]} - No se envían notificaciones de fin de turno")
                return resultado
            
            current_time = now.strftime("%H:%M")
            current_hour = now.hour
            current_minute = now.minute
            
            print(f"\n{'='*60}")
            print(f"🕐 VERIFICANDO NOTIFICACIONES DE FIN DE TURNO")
            print(f"⏰ Hora actual: {current_time}")
            print(f"{'='*60}\n")
            
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
                        print(f"   {operator_name}: Turno nocturno {start_time_str}-{end_time_str} - OMITIDO (sin notificación)")
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
                    print(f"   {operator_name}: Turno {start_time_str}-{end_time_str}, notificar a las {notification_hour:02d}:{notification_minute:02d}")
                    print(f"   En turno: {is_in_shift}, Hora actual: {current_hour:02d}:{current_minute:02d}")
                    
                    # Verificar si es el momento exacto de enviar la notificación (con margen de ±2 minutos)
                    time_diff = abs(current_minutes - notification_minutes)
                    
                    print(f"   Diferencia: {time_diff} minutos")
                    
                    # IMPORTANTE: Solo notificar si está en turno Y es el momento correcto
                    if is_in_shift and time_diff <= 2:  # Margen de 2 minutos
                        print(f"🔔 Es momento de notificar a {operator_name} (turno termina a las {end_time_str})")
                        
                        # Obtener todos los tickets asignados a este operador
                        all_tickets = self.splynx.get_assigned_tickets(group_id=SPLYNX_SUPPORT_GROUP_ID)
                        operator_tickets = [
                            ticket for ticket in all_tickets 
                            if int(ticket.get('assign_to', 0)) == person_id
                        ]
                        
                        print(f"📋 {operator_name} tiene {len(operator_tickets)} ticket(s) asignado(s)")
                        
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
            
            print(f"\n{'='*60}")
            print(f"✅ VERIFICACIÓN COMPLETADA")
            print(f"   Operadores notificados: {resultado['operadores_notificados']}")
            print(f"   Total tickets reportados: {resultado['total_tickets_reportados']}")
            print(f"   Errores: {resultado['errores']}")
            print(f"{'='*60}\n")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error general en notificaciones de fin de turno: {e}")
            resultado["errores"] += 1
            return resultado

    def assign_unassigned_tickets(self, group_id="4"):
        """Asigna tickets no asignados del grupo de Soporte Técnico usando round-robin
        
        Args:
            group_id: ID del grupo (default "4" para Soporte Técnico)
            
        Returns:
            dict: Resumen de la operación con estadísticas
        """
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
                print("No hay tickets sin asignar")
                return resultado
            
            print(f"\n{'='*60}")
            print(f"🎫 ASIGNANDO {len(tickets)} TICKETS NO ASIGNADOS")
            print(f"{'='*60}\n")
            
            for ticket in tickets:
                ticket_id = ticket.get('id')
                subject = ticket.get('subject', 'Sin asunto')
                customer_id = ticket.get('customer_id', 'N/A')
                
                try:
                    from app.interface.interfaces import AssignmentTrackerInterface
                    
                    # Obtener la siguiente persona a asignar SIN incrementar el contador
                    assigned_person_id = self.get_next_assignee()
                    
                    # Actualizar el ticket en Splynx
                    response = self.splynx.update_ticket_assignment(ticket_id, assigned_person_id)
                    
                    if response:
                        # Solo incrementar el contador si la asignación fue exitosa
                        AssignmentTrackerInterface.increment_count(assigned_person_id)
                        
                        resultado["asignados_exitosamente"] += 1
                        resultado["detalles"].append({
                            "ticket_id": ticket_id,
                            "subject": subject,
                            "customer_id": customer_id,
                            "assigned_to": assigned_person_id,
                            "estado": "ASIGNADO"
                        })
                        print(f"✅ Ticket {ticket_id} asignado a persona {assigned_person_id}")
                    else:
                        resultado["errores"] += 1
                        resultado["detalles"].append({
                            "ticket_id": ticket_id,
                            "subject": subject,
                            "estado": "ERROR",
                            "error": "No se pudo actualizar en Splynx"
                        })
                        print(f"❌ Error asignando ticket {ticket_id}")
                        
                except Exception as e:
                    resultado["errores"] += 1
                    resultado["detalles"].append({
                        "ticket_id": ticket_id,
                        "subject": subject,
                        "estado": "ERROR",
                        "error": str(e)
                    })
                    print(f"❌ Error procesando ticket {ticket_id}: {e}")
            
            print(f"\n{'='*60}")
            print(f"✅ ASIGNACIÓN COMPLETADA")
            print(f"   Total: {resultado['total_tickets']}")
            print(f"   Asignados: {resultado['asignados_exitosamente']}")
            print(f"   Errores: {resultado['errores']}")
            print(f"{'='*60}\n")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error general en asignación de tickets: {e}")
            resultado["errores"] = resultado["total_tickets"]
            return resultado
