"""
Funciones para ejecución en hilos
Estas funciones son versiones de las funciones de views.py que no dependen de Flask
"""

from app.services.splynx_services import SplynxServices
from app.services.ticket_manager import TicketManager
from app.services.selenium_multi_departamentos import SeleniumMultiDepartamentos
from app.utils.config import DEPARTAMENTOS


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


def thread_assign_unassigned_tickets():
    """Versión para hilos de assign_unassigned_tickets"""
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
