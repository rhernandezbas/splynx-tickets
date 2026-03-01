# ADR-001: Arquitectura del Sistema App Splynx

## Status
Accepted

## Context

Se necesita un sistema automatizado de gestión de tickets que integre Splynx (plataforma ISP) con Gestión Real (sistema de ticketing). El sistema debe asignar tickets automáticamente a operadores usando algoritmos de distribución justa, enviar notificaciones por WhatsApp y rastrear tiempos de respuesta.

## Decision

### Stack Tecnológico
- **Backend**: Flask (Python 3.10+) con SQLAlchemy ORM
- **Base de datos**: MySQL remota (190.7.234.37:3025)
- **Scheduler**: APScheduler para jobs periódicos
- **Ingesta de tickets**: Webhooks desde Gestión Real (ver ADR-003)
- **Notificaciones**: Evolution API para WhatsApp
- **Deployment**: Docker Compose con builds multi-stage
- **CI/CD**: GitHub Actions → SSH deploy a VPS

### Arquitectura por Capas

```
Routes (API endpoints)
  ↓
Services (lógica de negocio, integraciones)
  ↓
Interface (CRUD, patrón repositorio)
  ↓
Models (SQLAlchemy ORM)
  ↓
MySQL Database
```

1. **Capa de Modelos** (`app/models/`): SQLAlchemy ORM, todas las entidades del dominio
2. **Capa de Interfaz** (`app/interface/`): CRUD operations, patrón repositorio con BaseInterface
3. **Capa de Servicios** (`app/services/`): Lógica de negocio, integraciones externas (Splynx API, webhook processing, Evolution API)
4. **Capa de Rutas** (`app/routes/`): Endpoints REST, autenticación, autorización por roles
5. **Utilidades** (`app/utils/`): Configuración, scheduling, helpers, logging

### Operaciones Asíncronas

Las operaciones de larga duración se ejecutan en threads de background:
- Se pasa `current_app._get_current_object()` para acceso al contexto de Flask
- Patrón: `threading.Thread(target=func, args=(app,)).start()`

### Integración con Sistemas Externos

| Sistema | Método | Propósito |
|---------|--------|-----------|
| Splynx | REST API | Crear/cerrar tickets, obtener clientes |
| Gestión Real | Webhooks entrantes | Recibir tickets nuevos y cierres (ver ADR-003) |
| Evolution API | REST API | Notificaciones WhatsApp |

### Timezone

Todo el sistema opera en `America/Argentina/Buenos_Aires`.

## Consequences

### Positive
- Automatización completa del ciclo de vida de tickets
- Distribución justa de carga entre operadores
- Notificaciones en tiempo real por WhatsApp
- Configuración dinámica desde base de datos sin redeploy

### Negative
- Dependencia de webhooks de Gestión Real (si GR no envía, no se crea el ticket)
- Threads manuales en lugar de task queue (Celery)
- Base de datos remota introduce latencia

### Notes
- Puerto de la aplicación: 7842
- El frontend fue eliminado del repositorio; solo se exponen endpoints REST
