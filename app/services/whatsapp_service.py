"""
Servicio centralizado para el manejo de envíos de WhatsApp
Gestiona todos los tipos de mensajes y notificaciones por WhatsApp
"""

from typing import Optional, Dict, Any, List
from app.services.evolution_api import EvolutionAPIService
from app.utils.constants import (
    EVOLUTION_API_BASE_URL,
    EVOLUTION_API_KEY,
    EVOLUTION_INSTANCE_NAME
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppService:
    """Servicio para gestionar envíos de WhatsApp"""
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp con Evolution API"""
        self.evolution_api = EvolutionAPIService(
            base_url=EVOLUTION_API_BASE_URL,
            api_key=EVOLUTION_API_KEY,
            instance_name=EVOLUTION_INSTANCE_NAME
        )
    
    def get_operator_phone(self, person_id: int) -> Optional[str]:
        """
        Obtiene el número de WhatsApp de un operador desde la BD

        Args:
            person_id: ID del operador

        Returns:
            str: Número de WhatsApp o None si no existe
        """
        from app.interface.interfaces import OperatorConfigInterface
        operator = OperatorConfigInterface.get_by_person_id(person_id)
        return operator.whatsapp_number if operator else None
    
    def get_operator_name(self, person_id: int) -> str:
        """
        Obtiene el nombre de un operador desde la BD

        Args:
            person_id: ID del operador

        Returns:
            str: Nombre del operador
        """
        from app.interface.interfaces import OperatorConfigInterface
        operator = OperatorConfigInterface.get_by_person_id(person_id)
        return operator.name if operator else f"Operador {person_id}"
    
    def send_overdue_tickets_alert(self, person_id: int, tickets_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envía alerta de tickets vencidos agrupados para un operador
        
        Args:
            person_id: ID del operador
            tickets_list: Lista de tickets vencidos
            
        Returns:
            dict: Resultado del envío con estadísticas
        """
        phone_number = self.get_operator_phone(person_id)
        operator_name = self.get_operator_name(person_id)
        
        resultado = {
            "person_id": person_id,
            "operator_name": operator_name,
            "phone_number": phone_number,
            "tickets_count": len(tickets_list),
            "success": False,
            "error": None
        }
        
        if not phone_number:
            resultado["error"] = "Número de WhatsApp no configurado"
            logger.warning(f"⚠️  {operator_name} no tiene número de WhatsApp configurado")
            return resultado
        
        try:
            response = self.evolution_api.send_multiple_tickets_alert(
                phone_number=phone_number,
                tickets_list=tickets_list,
                operator_name=operator_name
            )
            
            if response:
                resultado["success"] = True
                logger.info(f"✅ Alerta enviada a {operator_name} ({len(tickets_list)} tickets)")
            else:
                resultado["error"] = "Error en respuesta de Evolution API"
                logger.error(f"❌ Error enviando alerta a {operator_name}")
                
        except Exception as e:
            resultado["error"] = str(e)
            logger.error(f"❌ Excepción enviando alerta a {operator_name}: {e}")
        
        return resultado
    
    def send_end_of_shift_summary(self, person_id: int, tickets_list: List[Dict[str, Any]], shift_end_time: str) -> Dict[str, Any]:
        """
        Envía resumen de fin de turno a un operador
        
        Args:
            person_id: ID del operador
            tickets_list: Lista de tickets pendientes
            shift_end_time: Hora de fin de turno (formato "HH:MM")
            
        Returns:
            dict: Resultado del envío con estadísticas
        """
        phone_number = self.get_operator_phone(person_id)
        operator_name = self.get_operator_name(person_id)
        
        resultado = {
            "person_id": person_id,
            "operator_name": operator_name,
            "phone_number": phone_number,
            "tickets_count": len(tickets_list),
            "shift_end_time": shift_end_time,
            "success": False,
            "error": None
        }
        
        if not phone_number:
            resultado["error"] = "Número de WhatsApp no configurado"
            logger.warning(f"⚠️  {operator_name} no tiene número de WhatsApp configurado")
            return resultado
        
        try:
            response = self.evolution_api.send_end_of_shift_summary(
                phone_number=phone_number,
                operator_name=operator_name,
                tickets_list=tickets_list,
                shift_end_time=shift_end_time
            )
            
            if response:
                resultado["success"] = True
                logger.info(f"✅ Resumen de fin de turno enviado a {operator_name} ({len(tickets_list)} tickets)")
            else:
                resultado["error"] = "Error en respuesta de Evolution API"
                logger.error(f"❌ Error enviando resumen a {operator_name}")
                
        except Exception as e:
            resultado["error"] = str(e)
            logger.error(f"❌ Excepción enviando resumen a {operator_name}: {e}")
        
        return resultado
    
    def send_single_ticket_alert(self, person_id: int, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía alerta de un solo ticket (legacy, usar send_overdue_tickets_alert preferentemente)
        
        Args:
            person_id: ID del operador
            ticket_data: Datos del ticket
            
        Returns:
            dict: Resultado del envío
        """
        phone_number = self.get_operator_phone(person_id)
        operator_name = self.get_operator_name(person_id)
        
        resultado = {
            "person_id": person_id,
            "operator_name": operator_name,
            "phone_number": phone_number,
            "success": False,
            "error": None
        }
        
        if not phone_number:
            resultado["error"] = "Número de WhatsApp no configurado"
            return resultado
        
        try:
            response = self.evolution_api.send_ticket_alert(
                phone_number=phone_number,
                ticket_id=ticket_data.get('id'),
                subject=ticket_data.get('subject'),
                customer_name=ticket_data.get('customer_name'),
                created_at=ticket_data.get('created_at'),
                minutes_elapsed=ticket_data.get('minutes_elapsed')
            )
            
            if response:
                resultado["success"] = True
            else:
                resultado["error"] = "Error en respuesta de Evolution API"
                
        except Exception as e:
            resultado["error"] = str(e)
        
        return resultado
    
    def send_ticket_assignment_notification(
        self, 
        person_id: int, 
        ticket_id: str,
        subject: str,
        customer_name: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Envía notificación cuando se asigna un ticket a un operador
        
        Args:
            person_id: ID del operador
            ticket_id: ID del ticket
            subject: Asunto del ticket
            customer_name: Nombre del cliente
            priority: Prioridad del ticket
            
        Returns:
            dict: Resultado del envío
        """
        phone_number = self.get_operator_phone(person_id)
        operator_name = self.get_operator_name(person_id)
        
        resultado = {
            "person_id": person_id,
            "operator_name": operator_name,
            "phone_number": phone_number,
            "ticket_id": ticket_id,
            "success": False,
            "error": None
        }
        
        if not phone_number:
            resultado["error"] = "Número de WhatsApp no configurado"
            return resultado
        
        # Emoji según prioridad
        priority_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "urgent": "🔴"
        }.get(priority.lower(), "🟡")
        
        # Construir mensaje
        message = f"""🎫 *NUEVO TICKET ASIGNADO*

Hola {operator_name},

Se te ha asignado un nuevo ticket:

{priority_emoji} *Ticket #{ticket_id}*
👤 Cliente: {customer_name}
📝 Asunto: {subject}
⚡ Prioridad: {priority.capitalize()}

Por favor, revisa y atiende este ticket lo antes posible.

_Sistema de Tickets Splynx_"""
        
        try:
            response = self.evolution_api.send_text_message(
                phone_number=phone_number,
                message=message
            )
            
            if response:
                resultado["success"] = True
                logger.info(f"✅ Notificación de asignación enviada a {operator_name} - Ticket #{ticket_id}")
            else:
                resultado["error"] = "Error en respuesta de Evolution API"
                logger.error(f"❌ Error enviando notificación de asignación a {operator_name}")
                
        except Exception as e:
            resultado["error"] = str(e)
            logger.error(f"❌ Excepción enviando notificación de asignación: {e}")
        
        return resultado
    
    def send_custom_message(self, person_id: int, message: str) -> Dict[str, Any]:
        """
        Envía un mensaje personalizado a un operador
        
        Args:
            person_id: ID del operador
            message: Mensaje a enviar
            
        Returns:
            dict: Resultado del envío
        """
        phone_number = self.get_operator_phone(person_id)
        operator_name = self.get_operator_name(person_id)
        
        resultado = {
            "person_id": person_id,
            "operator_name": operator_name,
            "phone_number": phone_number,
            "success": False,
            "error": None
        }
        
        if not phone_number:
            resultado["error"] = "Número de WhatsApp no configurado"
            return resultado
        
        try:
            response = self.evolution_api.send_text_message(
                phone_number=phone_number,
                message=message
            )
            
            if response:
                resultado["success"] = True
            else:
                resultado["error"] = "Error en respuesta de Evolution API"
                
        except Exception as e:
            resultado["error"] = str(e)
        
        return resultado
    
    def send_bulk_message(self, person_ids: List[int], message: str) -> Dict[str, Any]:
        """
        Envía el mismo mensaje a múltiples operadores
        
        Args:
            person_ids: Lista de IDs de operadores
            message: Mensaje a enviar
            
        Returns:
            dict: Resumen de envíos
        """
        resultado = {
            "total_operadores": len(person_ids),
            "enviados_exitosamente": 0,
            "errores": 0,
            "detalles": []
        }
        
        for person_id in person_ids:
            envio = self.send_custom_message(person_id, message)
            
            if envio["success"]:
                resultado["enviados_exitosamente"] += 1
            else:
                resultado["errores"] += 1
            
            resultado["detalles"].append(envio)
        
        return resultado
    
    def validate_operator_config(self, person_id: int) -> Dict[str, Any]:
        """
        Valida que un operador tenga toda la configuración necesaria desde la BD

        Args:
            person_id: ID del operador

        Returns:
            dict: Estado de la configuración
        """
        from app.interface.interfaces import OperatorConfigInterface
        operator = OperatorConfigInterface.get_by_person_id(person_id)

        if operator:
            return {
                "person_id": person_id,
                "has_phone": bool(operator.whatsapp_number),
                "has_name": bool(operator.name),
                "phone_number": operator.whatsapp_number,
                "name": operator.name,
                "is_valid": bool(operator.whatsapp_number and operator.name)
            }
        else:
            return {
                "person_id": person_id,
                "has_phone": False,
                "has_name": False,
                "phone_number": None,
                "name": None,
                "is_valid": False
            }
    
    def get_all_operators_config(self) -> List[Dict[str, Any]]:
        """
        Obtiene la configuración de todos los operadores desde la BD

        Returns:
            list: Lista con configuración de cada operador
        """
        from app.interface.interfaces import OperatorConfigInterface
        all_operators = OperatorConfigInterface.get_all()
        return [self.validate_operator_config(op.person_id) for op in all_operators]
