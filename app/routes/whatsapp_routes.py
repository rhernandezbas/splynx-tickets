"""
WhatsApp Routes - Endpoints para gestión de mensajes de WhatsApp
Refactorizado con decorador para eliminar duplicación de código
"""

from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from functools import wraps
from app.services.whatsapp_service import WhatsAppService
from app.services.evolution_api import EvolutionAPIService
from app.utils.constants import (
    EVOLUTION_API_BASE_URL,
    EVOLUTION_API_KEY,
    EVOLUTION_INSTANCE_NAME
)
from app.schemas.whatsapp_schemas import (
    SendTextMessageSchema,
    SendOverdueAlertSchema,
    SendShiftSummarySchema,
    SendAssignmentNotificationSchema,
    SendCustomMessageSchema,
    SendBulkMessageSchema
)
from app.routes.auth_routes import login_required, admin_required
from app.utils.logger import get_logger

logger = get_logger(__name__)

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')


def whatsapp_handler(schema_class=None):
    """
    Decorador para manejar validación y errores en endpoints de WhatsApp.
    Elimina duplicación de código try-except en cada endpoint.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Validar input si se proporciona schema
                if schema_class:
                    schema = schema_class()
                    data = schema.load(request.get_json())
                    kwargs['validated_data'] = data

                # Ejecutar la función del endpoint
                return f(*args, **kwargs)

            except ValidationError as e:
                logger.warning(f"⚠️  Validación fallida en {f.__name__}: {e.messages}")
                return jsonify({
                    'success': False,
                    'error': 'Datos de entrada inválidos',
                    'details': e.messages
                }), 400

            except Exception as e:
                logger.error(f"❌ Error en {f.__name__}: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Error interno del servidor'
                }), 500

        return wrapper
    return decorator


def build_service_response(result):
    """
    Construye respuesta estandarizada para endpoints que usan WhatsAppService.
    Retorna tupla (dict, status_code).
    """
    if result['success']:
        return jsonify({
            'success': True,
            'message': f"Operación exitosa para {result['operator_name']}",
            'data': result
        }), 200
    else:
        status_code = 404 if result['error'] == "Número de WhatsApp no configurado" else 500
        return jsonify({
            'success': False,
            'error': result['error'],
            'data': result
        }), status_code


@whatsapp_bp.route('/send/text', methods=['POST'])
@whatsapp_handler(SendTextMessageSchema)
def send_text_message(validated_data):
    """
    Envía un mensaje de texto directo a un número de WhatsApp.
    Requiere permisos de administrador.
    """
    evolution_api = EvolutionAPIService(
        base_url=EVOLUTION_API_BASE_URL,
        api_key=EVOLUTION_API_KEY,
        instance_name=EVOLUTION_INSTANCE_NAME
    )

    response = evolution_api.send_text_message(
        phone_number=validated_data['phone_number'],
        message=validated_data['message']
    )

    if response:
        return jsonify({
            'success': True,
            'message': 'Mensaje enviado exitosamente',
            'data': {
                'phone_number': validated_data['phone_number'],
                'response': response
            }
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'Error enviando mensaje a Evolution API'
        }), 500


@whatsapp_bp.route('/send/overdue-alert', methods=['POST'])
@admin_required
@whatsapp_handler(SendOverdueAlertSchema)
def send_overdue_alert(validated_data):
    """
    Envía alerta de tickets vencidos agrupados a un operador.
    Requiere permisos de administrador.
    """
    whatsapp_service = WhatsAppService()
    result = whatsapp_service.send_overdue_tickets_alert(
        person_id=validated_data['person_id'],
        tickets_list=validated_data['tickets_list']
    )
    return build_service_response(result)


@whatsapp_bp.route('/send/shift-summary', methods=['POST'])
@admin_required
@whatsapp_handler(SendShiftSummarySchema)
def send_shift_summary(validated_data):
    """
    Envía resumen de fin de turno a un operador.
    Requiere permisos de administrador.
    """
    whatsapp_service = WhatsAppService()
    result = whatsapp_service.send_end_of_shift_summary(
        person_id=validated_data['person_id'],
        tickets_list=validated_data['tickets_list'],
        shift_end_time=validated_data['shift_end_time']
    )
    return build_service_response(result)


@whatsapp_bp.route('/send/assignment', methods=['POST'])
@admin_required
@whatsapp_handler(SendAssignmentNotificationSchema)
def send_assignment_notification(validated_data):
    """
    Envía notificación de asignación de ticket a un operador.
    Requiere permisos de administrador.
    """
    whatsapp_service = WhatsAppService()
    result = whatsapp_service.send_ticket_assignment_notification(
        person_id=validated_data['person_id'],
        ticket_id=validated_data['ticket_id'],
        subject=validated_data['subject'],
        customer_name=validated_data['customer_name'],
        priority=validated_data.get('priority', 'medium')
    )
    return build_service_response(result)


@whatsapp_bp.route('/send/custom', methods=['POST'])
@admin_required
@whatsapp_handler(SendCustomMessageSchema)
def send_custom_message(validated_data):
    """
    Envía un mensaje personalizado a un operador.
    Requiere permisos de administrador.
    """
    whatsapp_service = WhatsAppService()
    result = whatsapp_service.send_custom_message(
        person_id=validated_data['person_id'],
        message=validated_data['message']
    )
    return build_service_response(result)


@whatsapp_bp.route('/send/bulk', methods=['POST'])
@admin_required
@whatsapp_handler(SendBulkMessageSchema)
def send_bulk_message(validated_data):
    """
    Envía el mismo mensaje a múltiples operadores (máximo 50).
    Requiere permisos de administrador.
    """
    whatsapp_service = WhatsAppService()
    result = whatsapp_service.send_bulk_message(
        person_ids=validated_data['person_ids'],
        message=validated_data['message']
    )

    return jsonify({
        'success': True,
        'message': f"Mensajes procesados: {result['enviados_exitosamente']}/{result['total_operadores']}",
        'data': result
    }), 200


@whatsapp_bp.route('/operators/<int:person_id>/validate', methods=['GET'])
@login_required
@whatsapp_handler()
def validate_operator_config(person_id):
    """
    Valida la configuración de WhatsApp de un operador.
    Requiere autenticación.
    """
    whatsapp_service = WhatsAppService()
    config = whatsapp_service.validate_operator_config(person_id)

    return jsonify({
        'success': True,
        'data': config
    }), 200


@whatsapp_bp.route('/operators/config', methods=['GET'])
@login_required
@whatsapp_handler()
def get_all_operators_config():
    """
    Obtiene la configuración de WhatsApp de todos los operadores.
    Requiere autenticación.
    """
    whatsapp_service = WhatsAppService()
    configs = whatsapp_service.get_all_operators_config()

    return jsonify({
        'success': True,
        'total_operators': len(configs),
        'data': configs
    }), 200


@whatsapp_bp.route('/health', methods=['GET'])
@whatsapp_handler()
def health_check():
    """
    Verifica que el servicio de WhatsApp esté disponible.
    No requiere autenticación (endpoint público).
    """
    # No exponer información sensible de configuración
    api_configured = bool(
        EVOLUTION_API_BASE_URL and
        EVOLUTION_API_KEY and
        EVOLUTION_INSTANCE_NAME
    )

    if not api_configured:
        return jsonify({
            'success': False,
            'error': 'Variables de entorno de Evolution API no configuradas'
        }), 500

    return jsonify({
        'success': True,
        'message': 'Servicio de WhatsApp disponible'
    }), 200
