---
tdr: "1.0"
id: "flask-conventions"
title: "Convenciones Flask del Proyecto"
summary: "Reglas de implementación para rutas, servicios, interfaces y patrones generales del backend Flask."
---

# rules

## Estructura de respuesta API
- SIEMPRE retornar JSON con la estructura: `{"success": bool, "message": str, "data": ...}`
- En error: `{"success": False, "error": str(e)}` con código HTTP apropiado
- Código 200 para éxito, 400 para error de validación, 500 para error interno

## Rutas y blueprints
- Cada módulo de rutas usa un `Blueprint` con `url_prefix`
- Rutas principales en `/api/tickets/`, admin en `/api/admin/`, auth en `/api/auth/`
- WhatsApp en `/api/whatsapp/`, logs en `/api/logs/`, devices en `/api/device-analysis/`
- Los endpoints de envío de WhatsApp requieren rol admin; los de lectura requieren autenticación

## Operaciones asíncronas
- Las operaciones de larga duración SIEMPRE se ejecutan en threads de background
- SIEMPRE pasar `current_app._get_current_object()` al thread para contexto Flask
- Patrón obligatorio:
  ```python
  app = current_app._get_current_object()
  hilo = threading.Thread(target=func, args=(app,))
  hilo.start()
  ```
- NUNCA ejecutar llamadas API externas en el thread principal

## Capa de interfaz (repositorio)
- Todas las operaciones CRUD pasan por `app/interface/`
- Hereda de `BaseInterface` para operaciones comunes
- Los errores de duplicate key se loguean como `info` (comportamiento esperado)
- Los errores de SQLAlchemy hacen rollback y se loguean como `error`
- SIEMPRE retornar `None` o `False` en error, NUNCA lanzar excepciones

## Configuración
- NUNCA hardcodear valores de configuración operativa
- SIEMPRE usar `ConfigHelper.get_int()`, `get_bool()`, `get_str()` con un default
- Credenciales sensibles van en variables de entorno (`.env`), NUNCA en código

## Logging
- SIEMPRE usar el logger centralizado: `from app.utils.logger import get_logger`
- Formato: `logger.info("✅ mensaje")`, `logger.warning("⚠️ mensaje")`, `logger.error("❌ mensaje")`
- NUNCA usar `print()` para logging

## Autenticación y autorización
- Autenticación basada en sesiones con RBAC
- Roles: `admin` (acceso completo) y `operator` (acceso limitado)
- Operadores vinculados a `person_id` para asignación de tickets
- Permisos a nivel de página en tabla `users`

## Timezone
- SIEMPRE usar `America/Argentina/Buenos_Aires`
- NUNCA usar UTC sin convertir a timezone local para lógica de negocio

code_refs:
  - "app/routes/views.py"
  - "app/routes/admin_routes.py"
  - "app/routes/auth_routes.py"
  - "app/interface/interfaces.py"
  - "app/utils/config_helper.py"
  - "app/utils/logger.py"
