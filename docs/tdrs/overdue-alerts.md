# TDR: Alertas de Tickets Vencidos y Pre-Alertas

## Estado
**Aprobado** — 2026-03-01

## Contexto

El sistema de tickets necesita alertar a los operadores cuando un ticket lleva demasiado tiempo sin ser actualizado. Además, se requiere un mecanismo de **pre-alerta** que avise al operador antes de que el ticket se considere vencido, dándole oportunidad de actuar a tiempo.

## Decisiones

### 1. Definición de ticket vencido

Un ticket se considera **vencido** cuando el campo `updated_at` en Splynx tiene más de `TICKET_ALERT_THRESHOLD_MINUTES` minutos (default: 60) respecto a la hora actual.

### 2. Pre-alerta

Se envía una **pre-alerta** cuando un ticket está a `TICKET_PRE_ALERT_MINUTES` minutos (default: 15) de alcanzar el umbral de vencimiento. Es decir, si el umbral es 60 min, la pre-alerta se activa a los 45 min sin actualización.

- La pre-alerta se envía **una sola vez** por ticket (controlado por `pre_alert_sent_at` en `IncidentsDetection`).
- Si el operador actualiza el ticket antes del vencimiento, la pre-alerta cumplió su función.
- El campo `pre_alert_sent_at` se resetea (NULL) cuando se detecta que el ticket fue actualizado (ya no cumple criterio de pre-alerta).

### 3. Configuración en base de datos

| Clave | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `TICKET_ALERT_THRESHOLD_MINUTES` | int | 60 | Minutos sin actualización para considerar vencido |
| `TICKET_PRE_ALERT_MINUTES` | int | 15 | Minutos antes del vencimiento para enviar pre-alerta |
| `TICKET_RENOTIFICATION_INTERVAL_MINUTES` | int | 60 | Intervalo mínimo entre re-notificaciones de tickets vencidos |
| `TICKET_UPDATE_THRESHOLD_MINUTES` | int | 60 | Umbral de actualización de tickets |
| `OUTHOUSE_NO_ALERT_MINUTES` | int | 120 | Minutos sin alerta para tickets en estado OutHouse |
| `WHATSAPP_ENABLED` | bool | true | Habilitar/deshabilitar envío de WhatsApp |

### 4. Anti-spam

- Para tickets **vencidos**: se verifica `last_alert_sent_at` en la tabla `tickets_detection` (modelo `IncidentsDetection`). Si la última alerta fue hace menos de `TICKET_RENOTIFICATION_INTERVAL_MINUTES`, no se re-envía.
- Para **pre-alertas**: se verifica `pre_alert_sent_at`. Si ya tiene valor, no se re-envía.
- **IMPORTANTE**: La tabla `ticket_response_metrics` está **deprecated** (todos sus métodos son no-op). El anti-spam debe usar `IncidentsDetection` mediante `IncidentsInterface.find_by_ticket_id()`.

### 5. Flujo de ejecución

El job `check_and_alert_overdue_tickets` corre cada 3 minutos y ejecuta:

1. Obtener tickets asignados desde Splynx
2. Para cada ticket, calcular `minutes_since_update`
3. **Filtro OutHouse**: si el ticket está en estado OutHouse y tiene menos de `OUTHOUSE_NO_ALERT_MINUTES`, saltar
4. **Pre-alerta**: si `(threshold - pre_alert_minutes) <= minutes_since_update < threshold`:
   - Buscar ticket local con `IncidentsInterface.find_by_ticket_id()`
   - Si existe y `pre_alert_sent_at` es NULL → agrupar para enviar pre-alerta
5. **Alerta vencido**: si `minutes_since_update >= threshold`:
   - Buscar ticket local para verificar `last_alert_sent_at` (anti-spam)
   - Si puede alertar → agrupar para enviar alerta de vencido
6. Enviar mensajes agrupados por operador (un mensaje por operador con todos sus tickets)
7. Actualizar campos `pre_alert_sent_at` y/o `last_alert_sent_at` después de enviar

### 6. Condiciones para enviar alertas

Las alertas (tanto pre-alerta como vencidas) solo se envían si:

- El operador está en su **horario de alertas** (`schedule_type='alert'` en `operator_schedule`)
- El operador tiene **notificaciones habilitadas** (`notifications_enabled=True` en `operator_config`)
- El operador tiene **número de WhatsApp** configurado
- **WhatsApp está habilitado** globalmente (`WHATSAPP_ENABLED=True` en `system_config`)

### 7. Formato de mensajes

**Pre-alerta** (mensaje diferenciado con emoji de reloj):
```
⏰ *PRE-ALERTA DE TICKETS*

Hola *{nombre}*,

Tienes *N* ticket(s) que vencerán en ~{minutos} minutos:

*1. Ticket #{id}*
   👤 {cliente}
   📝 {asunto}
   ⏱️ {min} min sin actualizar

📌 *Actualiza estos tickets para evitar que se marquen como vencidos.*
```

**Alerta de vencido** (formato actual con emoji de sirena):
```
🚨 *ALERTA DE TICKETS VENCIDOS*

Hola *{nombre}*,

Tienes *N* ticket(s) con más de 45 minutos sin respuesta:
...
```

### 8. Modelo de datos

Campo `pre_alert_sent_at` (DateTime, nullable) agregado a `IncidentsDetection` (`tickets_detection`).

## Consecuencias

- Los operadores recibirán aviso anticipado antes de que un ticket se considere vencido
- El anti-spam funciona correctamente usando `IncidentsDetection` en vez de la tabla deprecated
- La configuración es flexible y modificable desde el admin panel
