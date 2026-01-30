"""
Funciones para ejecución en hilos
Estas funciones son versiones de las funciones de views.py que no dependen de Flask
Optimizado con patrón Singleton para evitar múltiples logins
"""

from app.services.splynx_services_singleton import SplynxServicesSingleton
from app.services.ticket_manager import TicketManager
from app.services.selenium_multi_departamentos import SeleniumMultiDepartamentos
from app.utils.constants import DEPARTAMENTOS
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Instancia singleton global (se reutiliza en todos los threads)
_splynx_service = None


def get_splynx_service():
    """
    Obtiene la instancia singleton de SplynxServices.
    Thread-safe y reutilizable.
    """
    global _splynx_service
    if _splynx_service is None:
        _splynx_service = SplynxServicesSingleton()
    return _splynx_service


def thread_download_csv():
    """
    Versión para hilos de download_csv.
    Descarga CSV de Gestión Real y guarda en BD.
    Returns True solo si TODAS las descargas fueron exitosas.
    """
    logger.info("="*60)
    logger.info("🚀 INICIANDO DESCARGA DE CSV")
    logger.info("="*60)

    selenium = SeleniumMultiDepartamentos()
    total_departamentos = len(DEPARTAMENTOS)
    exitosos = 0
    fallidos = 0

    for dept_key in DEPARTAMENTOS:
        logger.info(f"📥 Descargando CSV para departamento: {dept_key}...")
        try:
            resultado = selenium.descargar_csv_departamento(dept_key)
            if resultado:
                exitosos += 1
                logger.info(f"✅ Descarga Y guardado exitoso para {dept_key}")
            else:
                fallidos += 1
                logger.error(f"❌ Descarga o guardado fallido para {dept_key}")
        except Exception as e:
            fallidos += 1
            logger.error(f"❌ Excepción descargando CSV para {dept_key}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    # Retornar True solo si TODAS las descargas fueron exitosas
    exito_completo = (fallidos == 0 and exitosos == total_departamentos)

    logger.info("="*60)
    if exito_completo:
        logger.info(f"✅ DESCARGA COMPLETADA: {exitosos}/{total_departamentos} departamentos exitosos")
    else:
        logger.error(f"❌ DESCARGA CON ERRORES: {exitosos} exitosos, {fallidos} fallidos de {total_departamentos}")
    logger.info("="*60)

    return exito_completo


def thread_close_tickets():
    """
    Versión para hilos de close_tickets.
    Limpia tickets cerrados de la BD.
    """
    sp = get_splynx_service()
    tk = TicketManager(sp)
    data = tk.clean_closed_ticket()
    logger.info("✅ Tickets cerrados eliminados")
    return data


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
