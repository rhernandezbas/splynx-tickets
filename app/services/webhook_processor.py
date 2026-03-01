"""
Webhook Processor - Processes pending webhook records into tickets.
"""

from app.interface.webhook_interface import HookNuevoTicketInterface
from app.interface.interfaces import IncidentsInterface
from app.utils.config_helper import ConfigHelper
from app.utils.logger import get_logger

logger = get_logger(__name__)


def process_pending_webhooks():
    """
    Process all unprocessed webhook records from hook_nuevo_ticket.
    Maps webhook fields to IncidentsDetection and creates new incident records.

    Returns:
        dict: Statistics about the processing run.
    """
    unprocessed = HookNuevoTicketInterface.get_unprocessed()

    if not unprocessed:
        logger.info("No hay webhooks pendientes de procesar")
        return {'processed': 0, 'duplicates': 0, 'skipped': 0, 'errors': 0}

    logger.info(f"Procesando {len(unprocessed)} webhooks pendientes...")

    processed = 0
    duplicates = 0
    skipped = 0
    errors = 0

    # Solo procesar tickets del motivo permitido para crear en Splynx (configurable desde BD)
    motivo_permitido = ConfigHelper.get('WEBHOOK_MOTIVO_PERMITIDO', 'General Soporte')

    for hook in unprocessed:
        try:
            motivo = hook.motivo_contacto or ""

            # Filtrar: solo el motivo permitido se crea en Splynx
            if motivo.strip().lower() != motivo_permitido.strip().lower():
                skipped += 1
                logger.info(f"Webhook {hook.id} omitido: motivo_contacto='{motivo}' (solo se procesa '{motivo_permitido}')")
                HookNuevoTicketInterface.mark_processed(hook.id)
                continue

            # Build display name: prefer nombre_usuario, fall back to nombre_empresa
            display_name = hook.nombre_usuario or hook.nombre_empresa or "Cliente"

            incident_data = {
                'Cliente': hook.numero_cliente,
                'Cliente_Nombre': display_name,
                'Asunto': hook.motivo_contacto or "Sin motivo",
                'Fecha_Creacion': hook.fecha_creado,
                'Ticket_ID': None,  # Will be filled when create_ticket() runs
                'Estado': 'PENDING',
                'Prioridad': 'medium',
                'is_created_splynx': False,
                'last_update': hook.received_at,
            }

            result = IncidentsInterface.create(incident_data)

            if result is not None:
                processed += 1
                logger.info(f"Webhook {hook.id} procesado -> incident id={result.id}")
            else:
                # create() returns None for duplicates (IntegrityError on Fecha_Creacion)
                duplicates += 1
                logger.info(f"Webhook {hook.id} duplicado (Fecha_Creacion={hook.fecha_creado})")

            # Mark as processed regardless (duplicate is still "handled")
            HookNuevoTicketInterface.mark_processed(hook.id)

        except Exception as e:
            errors += 1
            logger.error(f"Error procesando webhook {hook.id}: {e}")

    logger.info(
        f"Procesamiento completado: {processed} nuevos, {duplicates} duplicados, {skipped} omitidos (otro motivo), {errors} errores"
    )

    return {
        'processed': processed,
        'duplicates': duplicates,
        'skipped': skipped,
        'errors': errors,
    }
