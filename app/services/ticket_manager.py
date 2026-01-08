"""
Ticket Manager - Handles ticket filtering and cleanup operations
Separates business logic from API calls
"""


from app.services.splynx_services import SplynxServices


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

    def assign_ticket_fairly(self) -> int:
        """Asigna un ticket de forma justa usando round-robin.
        
        Returns:
            int: ID de la persona asignada
        """
        from app.interface.interfaces import AssignmentTrackerInterface
        
        person_id = AssignmentTrackerInterface.get_person_with_least_tickets(
            self.ASSIGNABLE_PERSONS
        )
        
        AssignmentTrackerInterface.increment_count(person_id)
        print(f"Ticket asignado a persona ID: {person_id}")
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
            asunto = ticket_data.get("Asunto", "")
            fecha_creacion = ticket_data.get("Fecha_Creacion", "")

            assigned_person_id = self.assign_ticket_fairly()
            
            ticket_data = {
                "Cliente": cliente,
                "Asunto": asunto,
                "note": f"Ticket creado automaticamente por Api Splynx, con fecha original de {fecha_creacion}",
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


