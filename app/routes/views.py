"""Views"""

import os
import threading
from flask import jsonify,current_app
from app.routes import blueprint
from app.routes.thread_functions import thread_download_csv, thread_close_tickets, thread_create_tickets, thread_assign_unassigned_tickets, thread_alert_overdue_tickets, thread_end_of_shift_notifications, thread_auto_unassign_after_shift


def _archivos_base_dir():
    """Retorna el directorio base para archivos"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", "archivos"))


@blueprint.route("/", methods=["GET"])
def health_check():
    """Health check endpoint para Docker y monitoreo"""
    print("🏥 Health check endpoint llamado")
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


@blueprint.route("/api/tickets/assign_unassigned", methods=["POST"])
def assign_unassigned():
    """Asigna tickets no asignados del grupo de Soporte Técnico usando round-robin"""
    try:
        hilo = threading.Thread(target=thread_assign_unassigned_tickets, args=(current_app._get_current_object(),))
        hilo.start()
        return jsonify({
            "success": True,
            "message": "Asignación de tickets no asignados iniciada"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@blueprint.route("/api/tickets/alert_overdue", methods=["POST"])
def alert_overdue_tickets():
    """Alerta sobre tickets asignados que superen 45 minutos sin respuesta"""
    try:
        hilo = threading.Thread(target=thread_alert_overdue_tickets, args=(current_app._get_current_object(),))
        hilo.start()
        return jsonify({
            "success": True,
            "message": "Verificación de tickets vencidos iniciada"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@blueprint.route("/api/tickets/end_of_shift_notifications", methods=["POST"])
def end_of_shift_notifications():
    """Envía notificaciones de resumen 1 hora antes del fin de turno"""
    try:
        hilo = threading.Thread(target=thread_end_of_shift_notifications, args=(current_app._get_current_object(),))
        hilo.start()
        return jsonify({
            "success": True,
            "message": "Verificación de notificaciones de fin de turno iniciada"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@blueprint.route("/api/system/pause", methods=["POST"])
def pause_system():
    """Pausa el sistema - detiene asignación automática y procesos"""
    try:
        from flask import request
        from app.utils.system_control import SystemControl
        
        data = request.get_json() or {}
        reason = data.get("reason", "Pausa manual")
        paused_by = data.get("paused_by", "manual")
        
        state = SystemControl.pause(reason=reason, paused_by=paused_by)
        
        return jsonify({
            "success": True,
            "message": "Sistema pausado exitosamente",
            "state": state
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@blueprint.route("/api/system/resume", methods=["POST"])
def resume_system():
    """Reanuda el sistema - reactiva asignación automática y procesos"""
    try:
        from flask import request
        from app.utils.system_control import SystemControl
        
        data = request.get_json() or {}
        resumed_by = data.get("resumed_by", "manual")
        
        state = SystemControl.resume(resumed_by=resumed_by)
        
        return jsonify({
            "success": True,
            "message": "Sistema reanudado exitosamente",
            "state": state
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@blueprint.route("/api/system/status", methods=["GET"])
def system_status():
    """Obtiene el estado actual del sistema"""
    try:
        from app.utils.system_control import SystemControl
        
        status = SystemControl.get_status()
        
        return jsonify({
            "success": True,
            "status": status
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@blueprint.route("/api/tickets/auto_unassign_after_shift", methods=["POST"])
def auto_unassign_after_shift():
    """Desasigna tickets automáticamente 1 hora después del fin de turno"""
    try:
        hilo = threading.Thread(target=thread_auto_unassign_after_shift, args=(current_app._get_current_object(),))
        hilo.start()
        return jsonify({
            "success": True,
            "message": "Verificación de desasignación automática iniciada"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
