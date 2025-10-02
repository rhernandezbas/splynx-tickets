"""
Funciones para ejecución en hilos
Estas funciones son versiones de las funciones de views.py que no dependen de Flask
"""

import os
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


def thread_tickets_summary():
    """Versión para hilos de tickets_summary"""
    sp = SplynxServices()
    tk = TicketManager(sp)
    data = tk.check_ticket_splynx()
    print("Tickets verificados y guardados en tickets_status.txt")
    return data


def thread_close_tickets():
    """Versión para hilos de close_tickets"""
    sp = SplynxServices()
    tk = TicketManager(sp)
    data = tk.clean_closed_ticket()
    print("Tickets cerrados eliminados")
    return data


def thread_create_tickets():
    """Versión para hilos de create_tickets"""
    sp = SplynxServices()
    tk = TicketManager(sp)
    items = tk.read_clientes_extraidos()
    
    try:
        for item in items:
            tk.create_ticket(item)
        print("Tickets creados exitosamente")
        return True
    except Exception as e:
        print(f"Error al crear tickets: {str(e)}")
        return False
