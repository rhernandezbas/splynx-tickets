# App Splynx - Visión General del Proyecto

## Descripción

App Splynx es un sistema automatizado de gestión de tickets que integra tres plataformas:

- **Suricata**: Sistema intermedio de gestión de tickets que envía webhooks al backend
- **Splynx**: Plataforma de gestión ISP donde se crean y gestionan los tickets
- **Evolution API**: Servicio de notificaciones WhatsApp

El sistema automatiza el ciclo completo: recepción de tickets por webhook desde Suricata, creación en Splynx, asignación justa a operadores, notificaciones por WhatsApp y seguimiento de tiempos de respuesta.

## Problema que Resuelve

Antes de App Splynx, los operadores debían:
1. Revisar manualmente Gestión Real para nuevos tickets
2. Crear tickets manualmente en Splynx
3. Coordinar entre ellos quién toma cada ticket
4. No había visibilidad de tickets vencidos o sin atender

## Usuarios del Sistema

### Administradores
- Configuran operadores, horarios y parámetros del sistema
- Pausan/reanudan operadores o el sistema completo
- Acceden a logs de auditoría y métricas
- Envían mensajes WhatsApp manuales

### Operadores
- Reciben tickets asignados automáticamente
- Reciben notificaciones WhatsApp de alertas y resúmenes
- Tienen vista limitada del sistema según permisos

## Flujo Principal de Negocio

```
Suricata → [Webhook POST /api/hooks/nuevo-ticket] → hook_nuevo_ticket (BD)
  → [Scheduler procesa webhooks cada 3 min] → Solo "General Soporte"
  → tickets_detection (BD) → [API Splynx crea tickets] → Splynx
  → [Algoritmo asigna operador] → Operador notificado vía WhatsApp
  → [Monitoreo continuo] → Alertas de tickets vencidos
  → [Fin de turno] → Resumen y auto-desasignación
```

## Operadores Actuales

| Person ID | Nombre | Turno |
|-----------|--------|-------|
| 10 | Gabriel | Día / Guardia fin de semana |
| 27 | Luis | Tarde |
| 37 | Cesareo | Día |
| 38 | Yaini | Tarde |

## Horarios de Operación

- **Días de semana**: 8:00 AM - 11:00 PM (Argentina)
- **Fines de semana**: 9:00 AM - 9:00 PM
- Fuera de estos horarios, el scheduler no ejecuta jobs

## Tipos de Notificación WhatsApp

1. **Asignación**: Cuando se asigna un ticket nuevo al operador
2. **Alerta de vencimiento**: Tickets sin actualizar por más de X minutos (configurable)
3. **Resumen de fin de turno**: 1 hora antes de que termine el turno
4. **Mensajes personalizados**: Enviados manualmente por admins

## Métricas Clave

- **Tiempo de respuesta**: Minutos desde asignación hasta primera acción
- **Tickets vencidos**: Tickets que superan el umbral sin actualización
- **Distribución de carga**: Tickets asignados por operador (tracked en assignment_tracker)
- **Conteo de alertas**: Cuántas veces se alertó sobre un ticket
