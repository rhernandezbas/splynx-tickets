# ADR-003: Migración de Selenium a Webhooks para Ingesta de Tickets

## Status
Accepted

## Context

El sistema originalmente usaba **Selenium + Chromium** para hacer scraping de CSV desde Gestión Real cada 3 minutos. Este enfoque presentaba múltiples problemas:

- **Fragilidad**: Dependencia de XPaths, selectores CSS y estructura de la UI de Gestión Real. Cualquier cambio en su interfaz rompía el scraping.
- **Peso**: Chromium en Docker agrega ~150MB a la imagen, aumentando tiempos de build y uso de memoria.
- **Latencia**: Polling cada 3 minutos implica hasta 3 minutos de retraso. El proceso de login + navegación + descarga agrega más tiempo.
- **Mantenibilidad**: Selenium requiere ChromeDriver compatible, configuración headless, y manejo de timeouts y errores del navegador.

Suricata (sistema intermedio de gestión de tickets) ahora envía webhooks HTTP cuando se crea o cierra un ticket.

## Decision

Reemplazar el pipeline **Selenium → CSV → DB** con un flujo **Webhook → DB → Procesamiento diferido**.

### Arquitectura del nuevo flujo

```
Suricata → POST /api/hooks/nuevo-ticket → hook_nuevo_ticket (BD)
  → [Scheduler cada 3 min] → process_pending_webhooks()
  → Solo motivo "General Soporte" se procesa
  → tickets_detection (BD) → create_ticket() en Splynx
  → Asignación + Notificación WhatsApp
```

### Normalización de campos

Suricata envía campos con nombres con espacios. El endpoint normaliza a snake_case antes de guardar:

| Campo Suricata | Campo modelo |
|---|---|
| `Nombre de la empresa` | `nombre_empresa` |
| `Numero de ticket` | `numero_ticket` |
| `Numero de  cliente` | `numero_cliente` |
| `Numero de  Whatsapp` | `numero_whatsapp` |
| `Motivo de contacto` | `motivo_contacto` |
| `Departamento creacion del ticket` | `departamento` |
| `Canal por el que entro el ticket` | `canal_entrada` |
| `Nombre y apellido del usuario` | `nombre_usuario` |

### Filtro por motivo de contacto

El webhook recibe tickets de todas las áreas, pero solo los de **"General Soporte"** se procesan para crear en Splynx. Los demás se guardan en `hook_nuevo_ticket` como auditoría pero se marcan como `processed=True` sin crear ticket. El motivo es configurable via `ConfigHelper` con la clave `WEBHOOK_MOTIVO_PERMITIDO`.

### Componentes

| Componente | Descripción |
|-----------|-------------|
| `POST /api/hooks/nuevo-ticket` | Endpoint webhook que recibe y persiste el payload |
| `POST /api/hooks/cierre-ticket` | Endpoint webhook de cierre (solo auditoría) |
| `hook_nuevo_ticket.processed` | Flag para tracking de procesamiento |
| `webhook_processor.py` | Servicio que mapea webhooks a tickets |
| `process_webhooks_job` | Scheduler job que reemplaza a `all_flow_job` |

### Procesamiento diferido

El webhook solo guarda en BD y responde inmediatamente. Un job del scheduler procesa los webhooks pendientes cada 3 minutos:
1. Query `hook_nuevo_ticket WHERE processed = False`
2. Mapear campos a `tickets_detection`
3. Marcar como `processed = True`
4. Ejecutar `create_ticket()` para crear en Splynx

### Mapeo de campos

| hook_nuevo_ticket | tickets_detection | Notas |
|---|---|---|
| `numero_cliente` | `Cliente` | ID del cliente |
| `nombre_usuario` / `nombre_empresa` | `Cliente_Nombre` | Nombre display |
| `motivo_contacto` | `Asunto` | Reemplaza "Ticket-FO"/"Ticket-WIRELESS" |
| `fecha_creado` | `Fecha_Creacion` | Clave de deduplicación |
| *(vacío)* | `Ticket_ID` | Se llena al crear en Splynx |
| `"PENDING"` | `Estado` | Estado inicial |
| `"medium"` | `Prioridad` | Default |

### Eliminaciones

- `app/services/selenium_multi_departamentos.py` (Selenium scraper)
- `app/services/tickets_process.py` (CSV parser)
- `app/archivos/` (directorio de CSVs temporales)
- Dependencia `selenium` de `pyproject.toml`
- Chromium y ChromeDriver del Dockerfile
- Campos `is_from_gestion_real` y `ultimo_contacto_gr` de `tickets_detection`
- Variables de entorno `GESTION_REAL_USERNAME`, `GESTION_REAL_PASSWORD`
- Constantes `DEPARTAMENTOS`, `DEPARTAMENTOS_SELENIUM`, `LOGIN_URL`, `CASOS_URL`

## Consequences

### Positive
- **Imagen Docker más liviana**: ~150MB menos sin Chromium
- **Mayor confiabilidad**: Sin dependencia de scraping, selectores XPath, o sesiones de navegador
- **Menor latencia**: Webhook llega en tiempo real; procesamiento diferido cada 3 min mantiene el mismo ritmo
- **Menor complejidad**: Eliminación de Selenium, ChromeDriver, y toda la lógica de CSV
- **Datos más ricos**: El webhook trae `motivo_contacto`, `canal_entrada`, `numero_whatsapp` directamente

### Negative
- **Dependencia del webhook de Suricata**: Si Suricata no envía el webhook, no se crea el ticket
- **Sin autenticación en webhooks**: Actualmente los endpoints no validan el origen (decisión consciente, a mejorar)
- **Webhook de cierre es solo auditoría**: No auto-cierra tickets; la sincronización con Splynx sigue siendo la fuente de verdad para cierres
