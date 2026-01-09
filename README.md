# App Splynx - Sistema de Gestión de Tickets

Sistema automatizado para gestión de tickets con integración a Splynx y asignación justa de tickets.

## Característicass

- ✅ Integración con API de Splynx
- ✅ Asignación automática y equitativa de tickets entre múltiples personas
- ✅ Base de datos MySQL en la nube
- ✅ Sistema de tracking de asignaciones
- ✅ Prevención de duplicados
- ✅ Dockerizado para fácil despliegue

## Requisitos

- Docker y Docker Compose (para ejecución en contenedor)
- O Python 3.10+ y Poetry (para desarrollo local)

## Configuración de Base de Datos

La aplicación está configurada para conectarse a una base de datos MySQL en la nube:

- **Host**: 190.7.234.37:3025
- **Database**: ipnext
- **User**: mysql

Las credenciales se encuentran en `app/utils/config.py`.

## Ejecución con Docker

### Opción 1: Docker Compose (Recomendado)

```bash
# Construir y ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

### Opción 2: Docker directo

```bash
# Construir la imagen
docker build -t app-splynx:latest .

# Ejecutar el contenedor
docker run -d \
  --name app-splynx \
  -p 5605:5605 \
  app-splynx:latest

# Ver logs
docker logs -f app-splynx

# Detener y eliminar
docker stop app-splynx
docker rm app-splynx
```

## Ejecución Local (Desarrollo)

```bash
# Instalar dependencias
poetry install

# Ejecutar migraciones (primera vez)
poetry run python run_migration.py

# Verificar conexión a BD
poetry run python test_connection.py

# Ejecutar aplicación
poetry run python -m flask run --host=0.0.0.0 --port=5605
```

## Endpoints API

### Tickets

- `POST /api/tickets/download` - Descargar CSV de tickets
- `POST /api/tickets/close` - Cerrar tickets
- `POST /api/tickets/create` - Crear tickets en Splynx
- `POST /api/tickets/all_flow` - Ejecutar flujo completo (download → create)

## Sistema de Asignación Justa

Los tickets se asignan automáticamente de forma equitativa entre:
- Persona ID: 10
- Persona ID: 27
- Persona ID: 37
- Persona ID: 38

El sistema usa un algoritmo round-robin que asigna cada ticket a la persona con menos tickets asignados.

## Estructura del Proyecto

```
app_splynx/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   └── models.py          # Modelos de BD
│   ├── interface/
│   │   └── interfaces.py      # Interfaces CRUD
│   ├── services/
│   │   ├── splynx_services.py # API Splynx
│   │   └── ticket_manager.py  # Lógica de tickets
│   ├── routes/
│   │   ├── views.py           # Endpoints
│   │   └── thread_functions.py
│   └── utils/
│       └── config.py          # Configuración
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Migraciones

Para crear las tablas en una base de datos nueva:

```bash
# Con Docker
docker exec -it app-splynx python run_migration.py

# Local
poetry run python run_migration.py
```

## Troubleshooting

### Error de conexión a MySQL

Verificar que:
1. El servidor MySQL está accesible desde tu red
2. Las credenciales son correctas
3. El puerto 3025 está abierto

### Error de cryptography

Si ves errores relacionados con `cryptography`, asegúrate de que el paquete está instalado:

```bash
poetry add cryptography
```

## Logs

```bash
# Docker Compose
docker-compose logs -f app

# Docker directo
docker logs -f app-splynx
```

## Mantenimiento

### Resetear contadores de asignación

```python
from app.interface.interfaces import AssignmentTrackerInterface
AssignmentTrackerInterface.reset_all_counts()
```

### Ver estadísticas de asignación

```python
from app.interface.interfaces import AssignmentTrackerInterface
trackers = AssignmentTrackerInterface.get_all()
for tracker in trackers:
    print(f"Persona {tracker.person_id}: {tracker.ticket_count} tickets")
```

## Licencia

Privado - Uso interno
