"""
Funciones para ejecución en hilos
Estas funciones son versiones de las funciones de views.py que no dependen de Flask
"""

from app.services.splynx_services import SplynxServices
from app.services.ticket_manager import TicketManager
from app.services.selenium_multi_departamentos import SeleniumMultiDepartamentos
from app.utils.constants import DEPARTAMENTOS


def thread_download_csv():
    """Versión para hilos de download_csv"""
    for dept_key in DEPARTAMENTOS:
        print(f"Descargando CSV para {dept_key}...")
        selenium = SeleniumMultiDepartamentos()
        selenium.descargar_csv_departamento(dept_key)
    print("Descarga de CSV completada para todos los departamentos")
    return True

def thread_close_tickets():
    """Versión para hilos de close_tickets"""
    sp = SplynxServices()
    tk = TicketManager(sp)
    data = tk.clean_closed_ticket()
    print("Tickets cerrados eliminados")
    return data


def thread_create_tickets(app):
    """Versión para hilos de create_tickets"""
    with app.app_context():
        sp = SplynxServices()
        tk = TicketManager(sp)

        try:
            tk.create_ticket()
            print("Tickets creados exitosamente")
            return True
        except Exception as e:
            print(f"Error al crear tickets: {str(e)}")
            return False


def thread_assign_unassigned_tickets(app):
    """Versión para hilos de assign_unassigned_tickets"""
    with app.app_context():
        sp = SplynxServices()
        tk = TicketManager(sp)
        
        try:
            resultado = tk.assign_unassigned_tickets()
            print(f"Asignación completada: {resultado['asignados_exitosamente']} de {resultado['total_tickets']}")
            return resultado
        except Exception as e:
            print(f"Error al asignar tickets: {str(e)}")
            return {
                "total_tickets": 0,
                "asignados_exitosamente": 0,
                "errores": 1,
                "error": str(e)
            }


def thread_alert_overdue_tickets(app):
    """Versión para hilos de alert_overdue_tickets - Alerta sobre tickets con más de 45 minutos"""
    with app.app_context():
        from app.utils.constants import TICKET_ALERT_THRESHOLD_MINUTES
        
        sp = SplynxServices()
        tk = TicketManager(sp)
        
        try:
            resultado = tk.check_and_alert_overdue_tickets(threshold_minutes=TICKET_ALERT_THRESHOLD_MINUTES)
            print(f"Alertas completadas: {resultado['alertas_enviadas']} de {resultado['tickets_vencidos']} tickets vencidos")
            return resultado
        except Exception as e:
            print(f"Error al alertar tickets vencidos: {str(e)}")
            return {
                "total_tickets_revisados": 0,
                "tickets_vencidos": 0,
                "alertas_enviadas": 0,
                "errores": 1,
                "error": str(e)
            }

def thread_end_of_shift_notifications(app):
    """Versión para hilos de end_of_shift_notifications - Envía resumen 1 hora antes del fin de turno"""
    with app.app_context():
        sp = SplynxServices()
        tk = TicketManager(sp)
        
        try:
            resultado = tk.send_end_of_shift_notifications()
            print(f"Notificaciones de fin de turno: {resultado['operadores_notificados']} operadores notificados")
            return resultado
        except Exception as e:
            print(f"Error al enviar notificaciones de fin de turno: {str(e)}")
            return {
                "operadores_notificados": 0,
                "total_tickets_reportados": 0,
                "errores": 1,
                "error": str(e)
            }

def thread_auto_unassign_after_shift(app):
    """Versión para hilos de auto_unassign_after_shift - Desasigna tickets 1 hora después del fin de turno"""
    with app.app_context():
        sp = SplynxServices()
        tk = TicketManager(sp)
        
        try:
            resultado = tk.auto_unassign_after_shift()
            print(f"Desasignación automática: {resultado['tickets_desasignados']} tickets desasignados de {resultado['tickets_revisados']} revisados")
            return resultado
        except Exception as e:
            print(f"Error en desasignación automática: {str(e)}")
            return {
                "tickets_revisados": 0,
                "tickets_desasignados": 0,
                "errores": 1,
                "error": str(e)
            }
