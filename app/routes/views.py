"""Views"""

import os
import threading
from flask import jsonify,current_app
from app.routes import blueprint
from app.routes.thread_functions import thread_download_csv, thread_close_tickets, thread_create_tickets


def _archivos_base_dir():
    """Retorna el directorio base para archivos"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", "archivos"))


@blueprint.route("/", methods=["GET"])
def health_check():
    """Health check endpoint para Docker y monitoreo"""
    return jsonify({
        "status": "healthy",
        "service": "splynx-tickets",
        "message": "Application is running"
    }), 200


@blueprint.route("/api/tickets/download", methods=["POST"])
def download_csv():
    """Descargar CSV para un departamento específico de forma asíncrona"""
    hilo = threading.Thread(target=thread_download_csv)
    hilo.start()
    return jsonify({
        "success": True,
        "message": "Descarga de CSV iniciada"
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
    app = current_app._get_current_object()  # Obtiene el objeto real de la aplicación
    hilo = threading.Thread(target=thread_create_tickets, args=(app,))
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

        create_tickets()
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
