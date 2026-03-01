---
tdr: "1.0"
id: "ticket-assignment"
title: "Algoritmo de Asignación de Tickets"
summary: "Reglas técnicas del algoritmo de distribución justa de tickets entre operadores."
---

# rules

## Algoritmo de asignación (get_next_assignee)
- El algoritmo se ejecuta en `ticket_manager.py` método `get_next_assignee()`
- Los operadores asignables por defecto son: person_id `[10, 27, 37, 38]`
- El orden de evaluación es estricto y no debe alterarse:
  1. Verificar si es fin de semana → asignar a operador de guardia (ID 10)
  2. Parsear tags del ticket note (`[TT]` o `[TD]`)
  3. Consultar schedules de tipo `assignment`
  4. Filtrar operadores disponibles (no pausados, en horario)
  5. Asignar al operador con menos tickets (distribución justa)
  6. Fallback: round-robin si nadie disponible

## Tags de turno en notas de ticket
- `[TT]` (Turno Tarde): asignar a IDs 27, 38
- `[TD]` (Turno Día): asignar a IDs 10, 37
- Si no hay tag, se usa el algoritmo de distribución justa completo

## Estados de pausa de operador
- `is_paused=True`: Pausa total (sin asignaciones, sin notificaciones)
- `assignment_paused=True`: Sin nuevas asignaciones, pero mantiene tickets actuales
- `notifications_enabled=False`: Sin notificaciones WhatsApp, pero sí recibe asignaciones
- SIEMPRE verificar ambos estados de pausa antes de asignar

## Tracking de distribución justa
- La tabla `assignment_tracker` registra `ticket_count` por `person_id`
- Se asigna al operador con menor `ticket_count` entre los disponibles
- `last_assigned` se actualiza en cada asignación
- NUNCA resetear contadores manualmente sin razón operativa

## Reset automático de contadores por turno
- **Problema resuelto**: Operadores que entran en turnos posteriores tenían contador=0 mientras los demás acumulaban 15+, recibiendo TODOS los tickets nuevos hasta emparejarse
- **Solución**: Job `reset_assignment_counters_job` que resetea todos los contadores a 0 al inicio de cada turno
- **Configuración**: `ASSIGNMENT_RESET_HOURS` en `system_config` (string CSV, default `"8,16"`)
  - Ejemplo: `"8,16"` → reset a las 8:00 AM y 4:00 PM
  - Configurable vía `POST /api/admin/config`
- **Mecánica del job**:
  - Se ejecuta cada 1 minuto vía APScheduler
  - Verifica si `hora_actual` está en la lista de horas de reset Y `minuto <= 2` (ventana de ±2 min)
  - Llama a `AssignmentTrackerInterface.reset_all_counts()` para poner todos los `ticket_count` a 0
  - Usa timezone `America/Argentina/Buenos_Aires`
- **Reglas**:
  - El reset es global: afecta a TODOS los operadores en `assignment_tracker`
  - No depende de horario laboral (se ejecuta siempre, la verificación de hora es suficiente)
  - Si `ASSIGNMENT_RESET_HOURS` tiene valor inválido, usa fallback `[8, 16]`
  - El job NO resetea `last_assigned`, solo `ticket_count`

## Horarios de asignación
- Consultar `operator_schedule` con `schedule_type='assignment'`
- Formato de hora: HH:MM (24 horas)
- `day_of_week`: 0=Lunes, 6=Domingo
- Usar `ScheduleHelper.get_available_operators()` para obtener operadores disponibles
- NUNCA asignar tickets fuera del horario de asignación del operador

## Horarios de trabajo del sistema
- Días de semana: 8:00 AM - 11:00 PM (Argentina)
- Fines de semana: 9:00 AM - 9:00 PM (configurable en DB)
- Los jobs del scheduler NO se ejecutan fuera de estos horarios

## Sincronización de asignaciones desde Splynx
- El job `sync_tickets_status` (cada 5 min) detecta cambios de `assign_to` en Splynx
- Si `assigned_to` en Splynx difiere de la BD local, se actualiza `ticket.assigned_to`
- Cada cambio se registra en `ticket_reassignment_history` con `reassignment_type='splynx_sync'`
- El campo `notification_sent` (Boolean) registra si se envió la notificación WhatsApp
- **Mensajes diferenciados**:
  - Primera asignación (`old_assigned_to` es None/0): usa `send_ticket_assignment_notification` ("NUEVO TICKET ASIGNADO")
  - Reasignación (`old_assigned_to` tiene valor): usa `send_ticket_reassignment_notification` ("TICKET REASIGNADO" + operador anterior)
- Respeta `ConfigHelper.is_whatsapp_enabled()` y falla silenciosamente sin romper el sync
- La API de Splynx usa el campo `assign_to` (no `assigned_to`)

## Historial de reasignaciones
- Tabla `ticket_reassignment_history` registra todos los cambios de asignación
- Campos: `ticket_id`, `from/to_operator_id`, `from/to_operator_name`, `reason`, `reassignment_type`, `notification_sent`, `created_by`
- Tipos de reasignación: `splynx_sync`, `auto_unassign_after_shift`, `manual`
- Consultar vía `GET /api/admin/reassignment-history?ticket_id=X`

code_refs:
  - "app/services/ticket_manager.py"
  - "app/utils/schedule_helper.py"
  - "app/utils/scheduler.py"
  - "app/utils/sync_tickets_status.py"
  - "app/services/whatsapp_service.py"
  - "app/models/models.py"
  - "app/interface/interfaces.py"
  - "app/interface/reassignment_history.py"
