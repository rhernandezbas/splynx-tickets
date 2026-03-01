"""
Evolution API Service - Handles WhatsApp message sending
"""

import requests
from typing import Optional, Dict, Any, List
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EvolutionAPIService:
    """Service to interact with Evolution API for WhatsApp messaging"""
    
    def __init__(self, base_url: str, api_key: str, instance_name: str):
        """
        Initialize Evolution API service
        
        Args:
            base_url: Base URL of Evolution API (e.g., 'https://api.evolution.com')
            api_key: API key for authentication
            instance_name: Instance name for the WhatsApp connection
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.instance_name = instance_name
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key
        }
    
    def send_text_message(self, phone_number: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Send a text message via WhatsApp
        
        Args:
            phone_number: Phone number in format 5491112345678 (country code + number)
            message: Text message to send
            
        Returns:
            dict: Response from API or None if error
        """
        url = f"{self.base_url}/message/sendText/{self.instance_name}"
        
        payload = {
            "number": phone_number,
            "text": message
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"✅ Mensaje enviado a {phone_number}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando mensaje a {phone_number}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"📄 Response: {e.response.text}")
            return None
    
    def send_ticket_alert(self, phone_number: str, ticket_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a formatted ticket alert message
        
        Args:
            phone_number: Phone number to send alert to
            ticket_data: Dictionary containing ticket information
            
        Returns:
            dict: Response from API or None if error
        """
        ticket_id = ticket_data.get('id', 'N/A')
        subject = ticket_data.get('subject', 'Sin asunto')
        customer_name = ticket_data.get('customer_name', 'Cliente desconocido')
        created_at = ticket_data.get('created_at', 'N/A')
        minutes_elapsed = ticket_data.get('minutes_elapsed', 0)
        
        message = f"""🚨 *ALERTA DE TICKET*

📋 *Ticket ID:* {ticket_id}
👤 *Cliente:* {customer_name}
📝 *Asunto:* {subject}
🕐 *Creado:* {created_at}
⏱️ *Tiempo transcurrido:* {minutes_elapsed} minutos

⚠️ Este ticket lleva más de 60 minutos asignado sin respuesta.
Por favor, revisa y actualiza el estado del ticket."""
        
        return self.send_text_message(phone_number, message)
    
    def send_multiple_tickets_alert(self, phone_number: str, tickets_list: list, operator_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Send a formatted alert message with multiple tickets grouped together
        
        Args:
            phone_number: Phone number to send alert to
            tickets_list: List of dictionaries containing ticket information
            operator_name: Name of the operator (optional)
            
        Returns:
            dict: Response from API or None if error
        """
        if not tickets_list:
            return None
        
        total_tickets = len(tickets_list)
        
        # Encabezado del mensaje con nombre del operador si está disponible
        greeting = f"Hola *{operator_name}*,\n\n" if operator_name else ""
        
        message = f"""🚨 *ALERTA DE TICKETS VENCIDOS*

{greeting}Tienes *{total_tickets}* ticket{'s' if total_tickets > 1 else ''} con más de 60 minutos sin respuesta:

"""
        
        # Agregar cada ticket a la lista
        for idx, ticket_data in enumerate(tickets_list, 1):
            ticket_id = ticket_data.get('id', 'N/A')
            subject = ticket_data.get('subject', 'Sin asunto')
            customer_name = ticket_data.get('customer_name', 'Cliente desconocido')
            minutes_elapsed = ticket_data.get('minutes_elapsed', 0)
            
            # Limitar el asunto a 50 caracteres para mantener el mensaje compacto
            if len(subject) > 50:
                subject = subject[:47] + "..."
            
            message += f"""*{idx}. Ticket #{ticket_id}*
   👤 {customer_name}
   📝 {subject}
   ⏱️ {minutes_elapsed} min

"""
        
        # Pie del mensaje
        message += """⚠️ *Por favor, revisa y actualiza estos tickets lo antes posible.*"""
        
        return self.send_text_message(phone_number, message)
    
    def send_pre_alert_tickets(self, phone_number: str, tickets_list: list, operator_name: str = None, minutes_remaining: int = 15) -> Optional[Dict[str, Any]]:
        """
        Send a pre-alert message for tickets approaching the overdue threshold

        Args:
            phone_number: Phone number to send alert to
            tickets_list: List of dictionaries containing ticket information
            operator_name: Name of the operator (optional)
            minutes_remaining: Minutes remaining before tickets are considered overdue

        Returns:
            dict: Response from API or None if error
        """
        if not tickets_list:
            return None

        total_tickets = len(tickets_list)

        greeting = f"Hola *{operator_name}*,\n\n" if operator_name else ""

        message = f"""⏰ *PRE-ALERTA DE TICKETS*

{greeting}Tienes *{total_tickets}* ticket{'s' if total_tickets > 1 else ''} que vencerán en ~{minutes_remaining} minutos:

"""

        for idx, ticket_data in enumerate(tickets_list, 1):
            ticket_id = ticket_data.get('id', 'N/A')
            subject = ticket_data.get('subject', 'Sin asunto')
            customer_name = ticket_data.get('customer_name', 'Cliente desconocido')
            minutes_elapsed = ticket_data.get('minutes_elapsed', 0)

            if len(subject) > 50:
                subject = subject[:47] + "..."

            message += f"""*{idx}. Ticket #{ticket_id}*
   👤 {customer_name}
   📝 {subject}
   ⏱️ {minutes_elapsed} min sin actualizar

"""

        message += """📌 *Actualiza estos tickets para evitar que se marquen como vencidos.*"""

        return self.send_text_message(phone_number, message)

    def send_end_of_shift_summary(self, phone_number: str, operator_name: str, tickets_list: list, shift_end_time: str) -> Optional[Dict[str, Any]]:
        """
        Send end of shift summary with all pending tickets
        
        Args:
            phone_number: Phone number to send summary to
            operator_name: Name of the operator
            tickets_list: List of all pending tickets assigned to operator
            shift_end_time: Time when shift ends (e.g., "16:00")
            
        Returns:
            dict: Response from API or None if error
        """
        if not tickets_list:
            # Si no hay tickets, enviar mensaje de confirmación
            message = f"""✅ *RESUMEN DE FIN DE TURNO*

Hola *{operator_name}*,

Tu turno termina a las *{shift_end_time}*.

🎉 ¡Excelente trabajo! No tienes tickets pendientes asignados.

Que tengas un buen descanso."""
            return self.send_text_message(phone_number, message)
        
        total_tickets = len(tickets_list)
        
        # Encabezado del mensaje
        message = f"""📋 *RESUMEN DE FIN DE TURNO*

Hola *{operator_name}*,

Tu turno termina a las *{shift_end_time}* (en 1 hora).

Tienes *{total_tickets}* ticket{'s' if total_tickets > 1 else ''} pendiente{'s' if total_tickets > 1 else ''}:

"""
        
        # Agregar cada ticket a la lista
        for idx, ticket_data in enumerate(tickets_list, 1):
            ticket_id = ticket_data.get('id', 'N/A')
            subject = ticket_data.get('subject', 'Sin asunto')
            customer_name = ticket_data.get('customer_name', 'Cliente desconocido')
            status = ticket_data.get('status', 'Abierto')
            
            # Limitar el asunto a 50 caracteres
            if len(subject) > 50:
                subject = subject[:47] + "..."
            
            message += f"""*{idx}. Ticket #{ticket_id}*
   👤 {customer_name}
   📝 {subject}
   📊 Estado: {status}

"""
        
        # Pie del mensaje
        message += """⚠️ *Recuerda:*
• Actualizar el estado de los tickets
• Transferir tickets que no puedas completar
• Dejar notas para el siguiente turno

¡Gracias por tu trabajo hoy! 👏"""
        
        return self.send_text_message(phone_number, message)
    
    def send_bulk_alerts(self, phone_numbers: list, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send alert to multiple phone numbers
        
        Args:
            phone_numbers: List of phone numbers
            ticket_data: Dictionary containing ticket information
            
        Returns:
            dict: Summary of sent messages
        """
        results = {
            'total': len(phone_numbers),
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for phone in phone_numbers:
            response = self.send_ticket_alert(phone, ticket_data)
            if response:
                results['sent'] += 1
                results['details'].append({
                    'phone': phone,
                    'status': 'sent',
                    'response': response
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'phone': phone,
                    'status': 'failed'
                })
        
        return results
