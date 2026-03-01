"""
Funciones para ejecución en hilos
Estas funciones son versiones de las funciones de views.py que no dependen de Flask
Optimizado con patrón Singleton para evitar múltiples logins
"""

import threading
from app.services.splynx_services_singleton import SplynxServicesSingleton
from app.services.ticket_manager import TicketManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Instancia singleton global (se reutiliza en todos los threads)
_splynx_service = None
_splynx_lock = threading.Lock()


def get_splynx_service():
    """
    Obtiene la instancia singleton de SplynxServices.
    Thread-safe con lock.
    """
    global _splynx_service
    if _splynx_service is None:
        with _splynx_lock:
            if _splynx_service is None:
                _splynx_service = SplynxServicesSingleton()
    return _splynx_service


def thread_process_webhooks(app):
    """
    Procesa webhooks pendientes y crea tickets en Splynx.
    """
    with app.app_context():
        from app.services.webhook_processor import process_pending_webhooks

        try:
            # Step 1: Process pending webhooks into incidents
            result = process_pending_webhooks()
            logger.info(f"Webhooks procesados: {result['processed']} nuevos, {result['duplicates']} duplicados, {result['skipped']} omitidos, {result['errors']} errores")

            # Step 2: Create tickets in Splynx for new incidents
            sp = get_splynx_service()
            tk = TicketManager(sp)
            tk.create_ticket()
            logger.info("Tickets creados en Splynx exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error en thread_process_webhooks: {str(e)}")
            return False


def thread_create_tickets(app):
    """
    Versión para hilos de create_tickets.
    Lee tickets de BD y los crea en Splynx.
    """
    with app.app_context():
        sp = get_splynx_service()
        tk = TicketManager(sp)

        try:
            tk.create_ticket()
            logger.info("✅ Tickets creados exitosamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error al crear tickets: {str(e)}")
            return False


def thread_assign_unassigned_tickets(app):
    """
    Versión para hilos de assign_unassigned_tickets.
    Asigna tickets sin asignar usando round-robin y horarios.
    """
    with app.app_context():
        sp = get_splynx_service()
        tk = TicketManager(sp)

        try:
            resultado = tk.assign_unassigned_tickets()
            logger.info(f"✅ Asignación completada: {resultado['asignados_exitosamente']} de {resultado['total_tickets']}")
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al asignar tickets: {str(e)}")
            return {
                "total_tickets": 0,
                "asignados_exitosamente": 0,
                "errores": 1,
                "error": str(e)
            }


def thread_alert_overdue_tickets(app):
    """
    Versión para hilos de alert_overdue_tickets.
    Alerta sobre tickets vencidos (umbral configurable en BD).
    """
    with app.app_context():
        sp = get_splynx_service()
        tk = TicketManager(sp)

        try:
            # No pasar threshold_minutes para que se lea desde BD
            resultado = tk.check_and_alert_overdue_tickets()
            logger.info(f"✅ Alertas completadas: {resultado['alertas_enviadas']} de {resultado['tickets_vencidos']} tickets vencidos")
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al alertar tickets vencidos: {str(e)}")
            return {
                "total_tickets_revisados": 0,
                "tickets_vencidos": 0,
                "alertas_enviadas": 0,
                "errores": 1,
                "error": str(e)
            }


def thread_end_of_shift_notifications(app):
    """
    Versión para hilos de end_of_shift_notifications.
    Envía resumen 1 hora antes del fin de turno.
    """
    with app.app_context():
        sp = get_splynx_service()
        tk = TicketManager(sp)

        try:
            resultado = tk.send_end_of_shift_notifications()
            logger.info(f"✅ Notificaciones de fin de turno: {resultado['operadores_notificados']} operadores notificados")
            return resultado
        except Exception as e:
            logger.error(f"❌ Error al enviar notificaciones de fin de turno: {str(e)}")
            return {
                "operadores_notificados": 0,
                "total_tickets_reportados": 0,
                "errores": 1,
                "error": str(e)
            }


def thread_auto_unassign_after_shift(app):
    """
    Versión para hilos de auto_unassign_after_shift.
    Desasigna tickets 1 hora después del fin de turno.
    """
    with app.app_context():
        sp = get_splynx_service()
        tk = TicketManager(sp)

        try:
            resultado = tk.auto_unassign_after_shift()
            logger.info(f"✅ Desasignación automática: {resultado['tickets_desasignados']} tickets desasignados de {resultado['tickets_revisados']} revisados")
            return resultado
        except Exception as e:
            logger.error(f"❌ Error en desasignación automática: {str(e)}")
            return {
                "tickets_revisados": 0,
                "tickets_desasignados": 0,
                "errores": 1,
                "error": str(e)
            }
