"""
Splynx Webhooks Routes - Endpoints para recibir eventos desde Splynx.
Almacena payloads crudos para procesamiento posterior.
"""

import json
from flask import Blueprint, request, jsonify
from app.utils.config import db
from app.models.models import HookSplynxEvent
from app.utils.logger import get_logger

logger = get_logger(__name__)

splynx_webhooks_bp = Blueprint('splynx_webhooks', __name__, url_prefix='/api/hooks/splynx')


@splynx_webhooks_bp.route('/ticket-update', methods=['POST'])
def ticket_update():
    """Recibe eventos de actualización de tickets desde Splynx
    (cambios de asignación, cambios de estado, etc.) y los almacena para procesamiento posterior."""
    data = request.get_json(silent=True)
    if data is None:
        logger.warning(
            f"[WEBHOOK splynx/ticket-update] Body JSON vacío o Content-Type incorrecto. "
            f"Raw body: {request.get_data(as_text=True)[:500]}"
        )
        return jsonify({'success': False, 'error': 'Body JSON requerido'}), 400

    logger.info(f"[WEBHOOK splynx/ticket-update] Payload recibido: {json.dumps(data, default=str)[:1000]}")

    # Extraer event_type y ticket_id del payload si están presentes
    event_type = data.get('event_type', 'ticket_update')
    ticket_id = data.get('ticket_id') or data.get('id')

    try:
        record = HookSplynxEvent(
            event_type=str(event_type)[:50] if event_type else 'ticket_update',
            ticket_id=str(ticket_id)[:50] if ticket_id else None,
            payload=json.dumps(data, default=str),
        )
        db.session.add(record)
        db.session.commit()

        logger.info(
            f"[WEBHOOK splynx/ticket-update] Guardado OK: id={record.id}, "
            f"event_type={record.event_type}, ticket_id={record.ticket_id}"
        )
        return jsonify({'success': True, 'id': record.id}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"[WEBHOOK splynx/ticket-update] Error al guardar: {e}")
        return jsonify({'success': False, 'error': 'Error al guardar el evento'}), 500
