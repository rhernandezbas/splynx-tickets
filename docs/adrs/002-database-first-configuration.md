# ADR-002: Configuración Database-First

## Status
Accepted

## Context

El sistema necesita configuración dinámica sin redeploy. Parámetros como umbrales de alerta, intervalos de renotificación, horarios de operadores y toggles del sistema cambian frecuentemente y deben ser modificables desde el panel de administración.

## Decision

### Configuración en Base de Datos

Toda la configuración operativa se almacena en la tabla `system_config` y se accede mediante `ConfigHelper`:

```python
# ❌ NO hardcodear valores
THRESHOLD = 45

# ✅ Usar ConfigHelper con default
threshold = ConfigHelper.get_int('TICKET_ALERT_THRESHOLD_MINUTES', 45)
```

### Tablas de Configuración

| Tabla | Propósito |
|-------|-----------|
| `system_config` | Configuración global (umbrales, intervalos, toggles) |
| `operator_config` | Configuración por operador (nombres, WhatsApp, estados de pausa) |
| `operator_schedule` | Horarios por operador (trabajo, asignación, alertas) |

### ConfigHelper: Patrón de Acceso

Clase estática con cache en memoria:
- `ConfigHelper.get_config(key, default)` - Getter genérico
- `ConfigHelper.get_int(key, default)` - Integer type-safe
- `ConfigHelper.get_bool(key, default)` - Boolean type-safe
- `ConfigHelper.get_str(key, default)` - String type-safe
- `ConfigHelper.clear_cache()` - Invalidar cache

### Claves de Configuración Conocidas

| Clave | Tipo | Default | Propósito |
|-------|------|---------|-----------|
| `TICKET_ALERT_THRESHOLD_MINUTES` | int | 60 | Umbral para alerta de ticket sin actualizar |
| `TICKET_UPDATE_THRESHOLD_MINUTES` | int | 60 | Umbral de actualización |
| `TICKET_RENOTIFICATION_INTERVAL_MINUTES` | int | 60 | Intervalo de renotificación |
| `END_OF_SHIFT_NOTIFICATION_MINUTES` | int | 60 | Minutos antes de fin de turno para notificar |
| `OUTHOUSE_NO_ALERT_MINUTES` | int | 120 | Minutos sin alerta para tickets externos |
| `WHATSAPP_ENABLED` | bool | True | Toggle global de WhatsApp |

### Credenciales en Variables de Entorno

A diferencia de la configuración operativa, las credenciales sensibles van en `.env`:
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`
- `SPLYNX_USER`, `SPLYNX_PASSWORD`
- `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_NAME`
- `SECRET_KEY`

## Consequences

### Positive
- Cambios de configuración sin redeploy
- Configuración auditable en base de datos
- Cache en memoria para rendimiento
- Defaults seguros en código

### Negative
- Dependencia de la base de datos para arrancar la app
- Cache puede mostrar valores desactualizados brevemente
