# 🚀 Inicio Rápido - Panel de Administración

## Instalación en 3 Pasos

### 1️⃣ Migrar Base de Datos

```bash
cd /Users/rhernandezba/Downloads/Ipnext/app_splynx
mysql -u mysql -p -h 190.7.234.37 -P 3025 ipnext < migrations/create_admin_tables.sql
```

**Contraseña**: 1234

Esto creará las tablas:
- `operator_config`
- `operator_schedule`
- `system_config`
- `audit_log`

### 2️⃣ Instalar Dependencias Frontend

```bash
cd frontend
npm install
```

### 3️⃣ Iniciar Panel

**Opción A - Script Automático** (Recomendado):
```bash
./start_admin_panel.sh
```

**Opción B - Manual**:
```bash
# Terminal 1 - Backend (si no está corriendo)
python -m app

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 🌐 Acceder al Panel

Abrir en navegador:
```
http://localhost:3000
```

## 📋 Verificación

### Verificar Backend
```bash
curl http://localhost:5605/api/admin/operators
```

Debe retornar JSON con lista de operadores.

### Verificar Frontend
Abrir `http://localhost:3000` - debe mostrar el dashboard.

## 🎯 Primeros Pasos

### 1. Ver Dashboard
- Ir a `http://localhost:3000`
- Ver estadísticas generales
- Verificar estado del sistema

### 2. Gestionar Operadores
- Click en "Operadores" en el menú
- Ver lista de operadores
- Probar pausar/reanudar un operador

### 3. Ver Horarios
- Click en "Horarios"
- Ver horarios configurados por operador

### 4. Configurar Sistema
- Click en "Configuración"
- Modificar umbrales de tiempo
- Activar/desactivar notificaciones

### 5. Ver Auditoría
- Click en "Auditoría"
- Ver registro de cambios

## 🔧 Funcionalidades Principales

### Pausar Operador
1. Ir a **Operadores**
2. Click en **Pausar** en la tarjeta del operador
3. Ingresar razón (ej: "Vacaciones")
4. Confirmar

### Reiniciar Contadores Round-Robin
1. Ir a **Dashboard**
2. Click en **Reiniciar Contadores**
3. Confirmar
4. Todos los contadores se resetean a 0

### Cambiar Umbral de Alertas
1. Ir a **Configuración**
2. Buscar `TICKET_ALERT_THRESHOLD_MINUTES`
3. Cambiar valor (ej: de 60 a 45)
4. Click en **Guardar** ✅

### Pausar Sistema Completo
1. Ir a **Dashboard**
2. Click en **Pausar Sistema** (botón rojo)
3. Confirmar
4. El sistema deja de asignar tickets

### Activar/Desactivar WhatsApp
1. Ir a **Configuración**
2. Buscar `WHATSAPP_ENABLED`
3. Cambiar a `true` o `false`
4. Click en **Guardar** ✅

## 🛑 Detener Panel

**Opción A - Script**:
```bash
./stop_admin_panel.sh
```

**Opción B - Manual**:
```bash
# Detener Frontend
lsof -ti:3000 | xargs kill -9

# Detener Backend (opcional)
lsof -ti:5605 | xargs kill -9
```

## 🐛 Problemas Comunes

### Error: "Cannot connect to API"
**Solución**:
```bash
# Verificar que backend esté corriendo
curl http://localhost:5605/api/system/status

# Si no responde, iniciar backend
python -m app
```

### Error: "Database connection failed"
**Solución**:
```bash
# Verificar conexión a MySQL
mysql -u mysql -p -h 190.7.234.37 -P 3025 ipnext -e "SHOW TABLES;"

# Verificar que existan las tablas
# Debe mostrar: operator_config, operator_schedule, system_config, audit_log
```

### Frontend no carga
**Solución**:
```bash
# Limpiar e instalar de nuevo
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Puerto 3000 ocupado
**Solución**:
```bash
# Ver qué está usando el puerto
lsof -i:3000

# Matar proceso
lsof -ti:3000 | xargs kill -9
```

## 📊 Datos de Prueba

Los operadores por defecto son:
- **Gabriel Romero** (ID: 10) - 08:00-16:00
- **Luis Sarco** (ID: 27) - 10:00-17:20
- **Cesareo Suarez** (ID: 37) - 08:00-15:00
- **Yaini Al** (ID: 38) - 16:00-23:00

## 🔐 Seguridad

⚠️ **IMPORTANTE**: Este panel NO tiene autenticación.

Para producción, implementar:
1. Sistema de login
2. JWT tokens
3. HTTPS
4. CORS específico

## 📚 Más Información

- **Documentación completa**: `ADMIN_PANEL_README.md`
- **Frontend**: `frontend/README.md`
- **Endpoints API**: Ver `ADMIN_PANEL_README.md` sección "Endpoints API"

## 💡 Tips

1. **Refrescar datos**: Click en botón "Actualizar" en cada página
2. **Ver cambios**: Todos los cambios se registran en "Auditoría"
3. **Pausar vs Desactivar**: 
   - Pausar = temporal (con razón)
   - Desactivar = permanente
4. **Notificaciones**: Se pueden desactivar por operador o globalmente
5. **Horarios**: Los cambios de horario requieren reiniciar el backend

## 🎉 ¡Listo!

El panel está funcionando. Explora las diferentes secciones y funcionalidades.

Para soporte, revisar:
- Logs del backend: `logs/`
- Consola del navegador: F12
- Auditoría en el panel
