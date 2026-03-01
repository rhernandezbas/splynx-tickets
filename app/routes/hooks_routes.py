"""
Hooks Routes - Endpoints para webhooks entrantes de tickets.
Recibe payloads desde sistemas externos (Splynx iclass u otros) y los persiste en BD.
"""

from flask import Blueprint, request, jsonify
from app.interface.webhook_interface import HookNuevoTicketInterface, HookCierreTicketInterface
from app.utils.logger import get_logger

logger = get_logger(__name__)

hooks_bp = Blueprint('hooks', __name__, url_prefix='/api/hooks')


@hooks_bp.route('/nuevo-ticket', methods=['POST'])
def nuevo_ticket():
    """Recibe payload de nuevo ticket y lo guarda en BD."""
    data = request.get_json(silent=True)
    logger.info(f"[WEBHOOK nuevo-ticket] Content-Type: {request.content_type} | Payload: {data}")
    if data is None:
        logger.warning(f"[WEBHOOK nuevo-ticket] Body JSON vacío o Content-Type incorrecto. Raw body: {request.get_data(as_text=True)[:500]}")
        return jsonify({'error': 'Body JSON requerido'}), 400

    # Validar campos requeridos
    numero_ticket = data.get('numero_ticket')
    if numero_ticket is None:
        logger.warning(f"[WEBHOOK nuevo-ticket] Falta numero_ticket. Payload: {data}")
        return jsonify({'error': 'Campo numero_ticket es requerido'}), 400
    try:
        int(numero_ticket)
    except (ValueError, TypeError):
        logger.warning(f"[WEBHOOK nuevo-ticket] numero_ticket no numérico: {numero_ticket}")
        return jsonify({'error': 'Campo numero_ticket debe ser numérico'}), 400

    if not data.get('numero_cliente'):
        logger.warning(f"[WEBHOOK nuevo-ticket] Falta numero_cliente. Payload: {data}")
        return jsonify({'error': 'Campo numero_cliente es requerido'}), 400

    record = HookNuevoTicketInterface.create(data)
    if record is None:
        return jsonify({'error': 'Error al guardar el registro'}), 500

    logger.info(f"[WEBHOOK nuevo-ticket] Guardado OK: id={record.id}, numero_ticket={numero_ticket}")
    return jsonify({'ok': True, 'id': record.id}), 200


@hooks_bp.route('/cierre-ticket', methods=['POST'])
def cierre_ticket():
    """Recibe payload de cierre de ticket y lo guarda en BD."""
    data = request.get_json(silent=True)
    logger.info(f"[WEBHOOK cierre-ticket] Content-Type: {request.content_type} | Payload: {data}")
    if data is None:
        logger.warning(f"[WEBHOOK cierre-ticket] Body JSON vacío o Content-Type incorrecto. Raw body: {request.get_data(as_text=True)[:500]}")
        return jsonify({'error': 'Body JSON requerido'}), 400

    record = HookCierreTicketInterface.create(data)
    if record is None:
        return jsonify({'error': 'Error al guardar el registro'}), 500

    logger.info(f"[WEBHOOK cierre-ticket] Guardado OK: id={record.id}, numero_ticket={data.get('numero_ticket')}")
    return jsonify({'ok': True, 'id': record.id}), 200
