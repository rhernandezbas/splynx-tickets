---
tdr: "1.0"
id: "ticket-reopen"
title: "Reapertura Automática de Tickets Cerrados en Splynx sin Cierre en GR"
summary: "Reglas técnicas para la reapertura automática de tickets cuando se cierran en Splynx pero no en Gestión Real."
---

# rules

## Problema
Los operadores a veces cierran tickets en Splynx pero olvidan cerrarlos en GR (Gestión Real). Esto deja el ticket en un estado inconsistente — cerrado en Splynx pero abierto en GR.

## Ventana de reapertura
- Cuando `sync_tickets_status` detecta un ticket cerrado en Splynx (`closed='1'`), NO se cierra inmediatamente
- Se marca `splynx_closed_at = now()` para iniciar una ventana de espera
- La ventana es configurable: `TICKET_REOPEN_WINDOW_MINUTES` en `system_config` (default: 7 minutos)

## Caso 1: Cierra Splynx, NO cierra GR
- `sync_tickets_status` detecta cierre en Splynx → marca `splynx_closed_at = now()`
- Pasan 7 minutos sin webhook de cierre de GR en `hook_cierre_ticket`
- `ticket_reopen_checker` detecta ventana expirada sin cierre GR
- Reabre ticket en Splynx (PUT `closed=0`, `status_id=1`)
- Marca `recreado += 1`, limpia `splynx_closed_at = NULL`
- Envía WhatsApp al operador notificando reapertura

## Caso 2: Cierra Splynx, cierra GR en <7 min
- `sync_tickets_status` detecta cierre → marca `splynx_closed_at = now()`
- Webhook de cierre de GR llega en <7 min (se guarda en `hook_cierre_ticket`)
- `ticket_reopen_checker` encuentra cierre de GR dentro de la ventana
- Cierra ticket normalmente (`is_closed=True`, `closed_at=now()`), limpia `splynx_closed_at = NULL`

## Caso 3: Cierra GR primero, luego Splynx
- Webhook de cierre de GR llega primero (se guarda en `hook_cierre_ticket`)
- `sync_tickets_status` detecta cierre en Splynx
- Verifica que ya existe cierre de GR para este `numero_ticket_gr` → cierra directamente sin ventana
- `splynx_closed_at` nunca se setea

## Modelo de datos
- Campo `numero_ticket_gr` (Integer, nullable) en `IncidentsDetection`: ID del ticket en Gestión Real, se llena desde `hook_nuevo_ticket.numero_ticket` al procesar el webhook
- Campo `splynx_closed_at` (DateTime, nullable) en `IncidentsDetection`: momento en que Splynx reportó cierre, marca inicio de la ventana de espera

## Job ticket_reopen_checker
- Se ejecuta cada 2 minutos vía APScheduler
- Busca tickets con `splynx_closed_at IS NOT NULL` y `is_closed = False`
- Para cada uno, verifica si la ventana expiró (`elapsed >= TICKET_REOPEN_WINDOW_MINUTES`)
- Si expiró, busca cierre de GR en `hook_cierre_ticket` por `numero_ticket_gr`
- Si hay cierre GR → cierra normalmente
- Si NO hay cierre GR → reabre en Splynx y notifica

## Configuración
- `TICKET_REOPEN_WINDOW_MINUTES` (int, default: 7) en `system_config`

## Método reopen_ticket en SplynxServicesSingleton
- PUT a `/api/2.0/admin/support/tickets/{ticket_id}` con `{"closed": "0", "status_id": "1"}`

code_refs:
  - "app/models/models.py"
  - "app/utils/sync_tickets_status.py"
  - "app/services/ticket_reopen_checker.py"
  - "app/services/splynx_services_singleton.py"
  - "app/interface/webhook_interface.py"
  - "app/services/whatsapp_service.py"
  - "app/utils/scheduler.py"
