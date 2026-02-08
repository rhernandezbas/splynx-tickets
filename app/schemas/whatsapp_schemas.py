"""
Schemas de validación para endpoints de WhatsApp
Usa Marshmallow para validar requests de la API
"""

from marshmallow import Schema, fields, validate, ValidationError


class SendTextMessageSchema(Schema):
    """Schema para envío de mensaje de texto simple"""
    phone_number = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=20),
        metadata={"description": "Número de teléfono con código de país (ej: 5491112345678)"}
    )
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=4096),
        metadata={"description": "Mensaje de texto a enviar"}
    )


class SendOverdueAlertSchema(Schema):
    """Schema para envío de alerta de tickets vencidos"""
    person_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        metadata={"description": "ID del operador"}
    )
    tickets_list = fields.List(
        fields.Dict(),
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Lista de tickets vencidos"}
    )


class SendShiftSummarySchema(Schema):
    """Schema para envío de resumen de fin de turno"""
    person_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        metadata={"description": "ID del operador"}
    )
    tickets_list = fields.List(
        fields.Dict(),
        required=True,
        metadata={"description": "Lista de tickets pendientes"}
    )
    shift_end_time = fields.Str(
        required=True,
        validate=validate.Regexp(r"^\d{2}:\d{2}$"),
        metadata={"description": "Hora de fin de turno (formato HH:MM)"}
    )


class SendAssignmentNotificationSchema(Schema):
    """Schema para notificación de asignación de ticket"""
    person_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        metadata={"description": "ID del operador"}
    )
    ticket_id = fields.Str(
        required=True,
        metadata={"description": "ID del ticket"}
    )
    subject = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=500),
        metadata={"description": "Asunto del ticket"}
    )
    customer_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200),
        metadata={"description": "Nombre del cliente"}
    )
    priority = fields.Str(
        load_default="medium",
        validate=validate.OneOf(["low", "medium", "high", "urgent"]),
        metadata={"description": "Prioridad del ticket"}
    )


class SendCustomMessageSchema(Schema):
    """Schema para envío de mensaje personalizado"""
    person_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        metadata={"description": "ID del operador"}
    )
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=4096),
        metadata={"description": "Mensaje personalizado"}
    )


class SendBulkMessageSchema(Schema):
    """Schema para envío masivo de mensajes"""
    person_ids = fields.List(
        fields.Int(validate=validate.Range(min=1)),
        required=True,
        validate=validate.Length(min=1, max=50),
        metadata={"description": "Lista de IDs de operadores (máximo 50)"}
    )
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=4096),
        metadata={"description": "Mensaje a enviar a todos los operadores"}
    )
