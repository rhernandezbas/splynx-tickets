"""Views"""


import os
import threading
from flask import jsonify, request, current_app

from app.services.splynx_services import SplynxServices
from app.services.ticket_manager import TicketManager
from app.services.tickets_process import main
from app.services.selenium_multi_departamentos import SeleniumMultiDepartamentos
from app.utils.config import DEPARTAMENTOS
from . import blueprint
from app.routes.thread_functions import thread_download_csv, thread_tickets_summary, thread_close_tickets, thread_create_tickets


def _archivos_base_dir():
    """Retorna el directorio base para archivos"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", "archivos"))


# Funciones para ejecución en hilos (sin jsonify)
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
    items = tk.read_tickets_status()
    
    try:
        for item in items:
            tk.create_ticket(item)
        print("Tickets creados exitosamente")
        return True
    except Exception as e:
        print(f"Error al crear tickets: {str(e)}")
        return False


@blueprint.route("/api/tickets/download", methods=["POST"])
def download_csv():
    """Descargar CSV para un departamento específico de forma asíncrona"""
    hilo = threading.Thread(target=thread_download_csv)
    hilo.start()
    return jsonify({
        "success": True,
        "message": "Descarga de CSV iniciada"
    }), 200


@blueprint.route("/api/tickets/summary", methods=["GET"])
def tickets_summary():
    """"""
    main()
    hilo = threading.Thread(target=thread_tickets_summary)
    hilo.start()
    return jsonify({
        "success": True,
        "message": "Tickets verificados y guardados en tickets_status.txt"
    }), 200


@blueprint.route("/api/tickets/close", methods=["POST"])
def close_tickets():
    """"""
    hilo = threading.Thread(target=thread_close_tickets)
    hilo.start()
    return jsonify({
        "success": True,
        "message": "Tickets cerrados eliminados"
    }), 200


@blueprint.route("/api/tickets/create", methods=["POST"])
def create_tickets():
    """"""
    hilo = threading.Thread(target=thread_create_tickets)
    hilo.start()
    return jsonify({
        "success": True,
    }), 200


@blueprint.route("/api/tickets/all_flow", methods=["POST"])
def all_flow_tickets():
    """Ejecuta procesos de tickets en secuencia, esperando a que cada uno termine"""
    try:
        # Primer hilo: download_csv
        print("Iniciando download_csv...")
        hilo1 = threading.Thread(target=thread_download_csv)
        hilo1.start()
        hilo1.join()  # Espera a que termine antes de continuar
        print("download_csv completado")


        # Cuarto hilo: create_tickets
        print("Iniciando create_tickets...")
        hilo4 = threading.Thread(target=thread_create_tickets)
        hilo4.start()
        hilo4.join()  # Espera a que termine antes de continuar
        print("create_tickets completado")

        return jsonify({
            "success": True,
            "message": "Todos los procesos completados en secuencia"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
