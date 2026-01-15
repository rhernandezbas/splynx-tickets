# Panel de Administración - Sistema de Tickets Splynx

Panel web moderno para administrar operadores, horarios, notificaciones y configuraciones del sistema de tickets.

## 🎯 Funcionalidades

### 1. Dashboard
- **Vista general del sistema** con métricas en tiempo real
- **Control del sistema**: Pausar/reanudar sistema completo
- **Estadísticas de operadores**: Tickets asignados, pendientes, resueltos
- **Gráficos interactivos**: Distribución de tickets por operador
- **Reinicio de contadores**: Reset del sistema round-robin
- **Métricas de rendimiento**: Tiempos de respuesta promedio

### 2. Gestión de Operadores
- **Pausar/Reanudar operadores** individualmente con razón
- **Activar/Desactivar** operadores del sistema
- **Control de notificaciones**: Habilitar/deshabilitar WhatsApp por operador
- **Vista de horarios**: Ver horarios configurados de cada operador
- **Estadísticas individuales**: Tickets asignados y manejados
- **Estado en tiempo real**: Activo, pausado o inactivo

### 3. Gestión de Horarios
- **Visualización completa** de horarios por operador
- **Horarios por día**: Lunes a Domingo
- **Múltiples turnos**: Soporte para varios horarios por día
- **Estado de horarios**: Activos o inactivos
- **Información contextual**: Horarios de fin de semana y guardias

### 4. Configuración del Sistema
- **Parámetros globales**: Umbrales de tiempo, notificaciones
- **Configuración por categorías**:
  - Notificaciones (WhatsApp, alertas)
  - Horarios (fin de semana, guardias)
  - Umbrales (tiempos de respuesta)
  - Sistema (pausas, estados)
- **Edición en tiempo real**: Cambios aplicados inmediatamente
- **Tipos de datos**: Boolean, Integer, String, JSON

### 5. Auditoría
- **Registro completo** de todas las acciones
- **Filtros avanzados**: Por acción, entidad, fecha
- **Trazabilidad**: Valores anteriores y nuevos
- **Información de usuario**: Quién, cuándo, desde dónde (IP)
- **Historial permanente**: No se pueden eliminar registros

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│         Frontend (React + Vite)         │
│   TailwindCSS + shadcn/ui + Recharts    │
└─────────────────┬───────────────────────┘
                  │ HTTP/REST
┌─────────────────▼───────────────────────┐
│         Backend API (Flask)             │
│     /api/admin/* endpoints              │
└─────────────────┬───────────────────────┘
                  │ SQLAlchemy
┌─────────────────▼───────────────────────┐
│         Base de Datos (MySQL)           │
│  operator_config, system_config, etc.   │
└─────────────────────────────────────────┘
```

## 📦 Instalación

### Backend (Flask)

1. **Ejecutar migración de base de datos**:
```bash
cd /Users/rhernandezba/Downloads/Ipnext/app_splynx
mysql -u mysql -p -h 190.7.234.37 -P 3025 ipnext < migrations/create_admin_tables.sql
```

2. **Verificar que el servidor Flask esté corriendo**:
```bash
# El servidor ya debe estar corriendo en el puerto 5605
# Si no, iniciar con:
python -m app
```

3. **Verificar endpoints**:
```bash
curl http://localhost:5605/api/admin/operators
curl http://localhost:5605/api/system/status
```

### Frontend (React)

1. **Instalar dependencias**:
```bash
cd frontend
npm install
```

2. **Configurar variables de entorno** (opcional):
```bash
# Crear archivo .env en frontend/
echo "VITE_API_URL=http://localhost:5605" > .env
```

3. **Iniciar servidor de desarrollo**:
```bash
npm run dev
```

4. **Acceder al panel**:
```
http://localhost:3000
```

## 🚀 Deployment

### Opción 1: Desarrollo Local
```bash
# Terminal 1 - Backend (ya corriendo)
cd /Users/rhernandezba/Downloads/Ipnext/app_splynx
python -m app

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Opción 2: Producción

**Backend**: Ya está en producción en el puerto 5605

**Frontend**:
```bash
cd frontend
npm run build
# Los archivos estáticos estarán en frontend/dist/
```

Servir con nginx o integrar en Flask:
```python
# En app/__init__.py
from flask import send_from_directory

@app.route('/')
def serve_frontend():
    return send_from_directory('frontend/dist', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend/dist', path)
```

### Opción 3: Docker (Recomendado)

Crear `frontend/Dockerfile`:
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Crear `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:5605;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📋 Endpoints API

### Operadores
- `GET /api/admin/operators` - Listar todos los operadores
- `GET /api/admin/operators/:id` - Obtener operador específico
- `PUT /api/admin/operators/:id` - Actualizar operador
- `POST /api/admin/operators/:id/pause` - Pausar operador
- `POST /api/admin/operators/:id/resume` - Reanudar operador
- `POST /api/admin/operators/create` - Crear operador

### Horarios
- `POST /api/admin/schedules` - Crear horario
- `PUT /api/admin/schedules/:id` - Actualizar horario
- `DELETE /api/admin/schedules/:id` - Eliminar horario

### Asignaciones
- `POST /api/admin/assignment/reset` - Reiniciar contadores
- `GET /api/admin/assignment/stats` - Estadísticas de asignación

### Configuración
- `GET /api/admin/config` - Listar configuraciones
- `GET /api/admin/config/:key` - Obtener configuración específica
- `PUT /api/admin/config/:key` - Actualizar configuración

### Auditoría
- `GET /api/admin/audit` - Obtener logs de auditoría

### Dashboard
- `GET /api/admin/dashboard/stats` - Estadísticas del dashboard
- `GET /api/admin/metrics/operator/:id` - Métricas de operador

### Sistema
- `GET /api/system/status` - Estado del sistema
- `POST /api/system/pause` - Pausar sistema
- `POST /api/system/resume` - Reanudar sistema

## 🗄️ Modelos de Base de Datos

### operator_config
```sql
- id (PK)
- person_id (UNIQUE)
- name
- whatsapp_number
- is_active
- is_paused
- paused_reason
- paused_at
- paused_by
- notifications_enabled
- created_at
- updated_at
```

### operator_schedule
```sql
- id (PK)
- person_id
- day_of_week (0-6)
- start_time (HH:MM)
- end_time (HH:MM)
- is_active
- created_at
- updated_at
```

### system_config
```sql
- id (PK)
- key (UNIQUE)
- value
- value_type (string, int, bool, json)
- description
- category
- updated_at
- updated_by
```

### audit_log
```sql
- id (PK)
- action
- entity_type
- entity_id
- old_value (JSON)
- new_value (JSON)
- performed_by
- performed_at
- ip_address
- notes
```

## 🔧 Configuraciones Disponibles

### Notificaciones
- `TICKET_ALERT_THRESHOLD_MINUTES` (60) - Tiempo para alertar tickets
- `TICKET_UPDATE_THRESHOLD_MINUTES` (60) - Tiempo desde última actualización
- `TICKET_RENOTIFICATION_INTERVAL_MINUTES` (60) - Intervalo entre notificaciones
- `END_OF_SHIFT_NOTIFICATION_MINUTES` (60) - Aviso antes de fin de turno
- `WHATSAPP_ENABLED` (true/false) - Habilitar WhatsApp
- `OUTHOUSE_NO_ALERT_MINUTES` (120) - Sin alerta para OutHouse

### Horarios
- `FINDE_HORA_INICIO` (9) - Inicio fin de semana
- `FINDE_HORA_FIN` (21) - Fin fin de semana
- `PERSONA_GUARDIA_FINDE` (10) - Operador de guardia

### Sistema
- `SYSTEM_PAUSED` (true/false) - Pausar sistema completo

## 🎨 Tecnologías Utilizadas

### Frontend
- **React 18** - Framework UI
- **Vite** - Build tool
- **React Router** - Navegación
- **TailwindCSS** - Estilos
- **shadcn/ui** - Componentes UI
- **Radix UI** - Primitivos accesibles
- **Recharts** - Gráficos
- **Axios** - Cliente HTTP
- **Lucide React** - Iconos

### Backend
- **Flask** - Framework web
- **SQLAlchemy** - ORM
- **MySQL** - Base de datos
- **PyMySQL** - Driver MySQL

## 📝 Uso

### Pausar un Operador
1. Ir a **Operadores**
2. Encontrar el operador
3. Click en **Pausar**
4. Ingresar razón de la pausa
5. Confirmar

### Reiniciar Contadores Round-Robin
1. Ir a **Dashboard**
2. Click en **Reiniciar Contadores**
3. Confirmar acción
4. Los contadores se resetean a 0

### Cambiar Horarios de Notificación
1. Ir a **Configuración**
2. Buscar `TICKET_ALERT_THRESHOLD_MINUTES`
3. Cambiar valor (en minutos)
4. Click en **Guardar**

### Ver Auditoría
1. Ir a **Auditoría**
2. Filtrar por acción o límite
3. Ver detalles de cada cambio

## 🔒 Seguridad

**IMPORTANTE**: Este panel NO tiene autenticación implementada. Para producción:

1. **Agregar autenticación**:
   - JWT tokens
   - Session-based auth
   - OAuth2

2. **Proteger endpoints**:
```python
from functools import wraps
from flask import request, jsonify

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not verify_token(token):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/operators', methods=['GET'])
@require_auth
def get_operators():
    # ...
```

3. **CORS en producción**:
```python
# Configurar CORS específico en lugar de "*"
response.headers["Access-Control-Allow-Origin"] = "https://admin.tudominio.com"
```

4. **HTTPS obligatorio** en producción

## 🐛 Troubleshooting

### Error: "Cannot connect to API"
- Verificar que Flask esté corriendo en puerto 5605
- Verificar CORS configurado correctamente
- Revisar logs del backend

### Error: "Database connection failed"
- Verificar credenciales MySQL en `constants.py`
- Verificar que las tablas existan (ejecutar migración)
- Revisar logs de MySQL

### Frontend no carga
- Verificar que `npm install` se ejecutó correctamente
- Limpiar cache: `rm -rf node_modules package-lock.json && npm install`
- Verificar puerto 3000 disponible

### Cambios no se reflejan
- Refrescar navegador (Ctrl+F5)
- Verificar que el backend esté procesando requests
- Revisar logs de auditoría

## 📞 Soporte

Para problemas o dudas:
1. Revisar logs del backend: `logs/`
2. Revisar consola del navegador (F12)
3. Verificar logs de auditoría en el panel
4. Revisar este README

## 🚀 Próximas Funcionalidades

- [ ] Autenticación y autorización
- [ ] Exportar reportes en PDF/Excel
- [ ] Notificaciones en tiempo real (WebSockets)
- [ ] Modo oscuro
- [ ] Gráficos históricos avanzados
- [ ] Configuración de horarios desde el panel
- [ ] Gestión de múltiples grupos de Splynx
- [ ] API de webhooks para integraciones
- [ ] Dashboard personalizable
- [ ] Alertas configurables por operador

## 📄 Licencia

Uso interno - IPNext
