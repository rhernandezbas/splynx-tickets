# 🔒 Sistema de Monitoreo y Protección del VPS

Sistema configurado para prevenir modificaciones no autorizadas en el código del VPS y mantener sincronización con desarrollo local.

---

## 🎯 Objetivo

**Proteger el código en producción** y asegurar que el flujo de desarrollo sea:

```
Local → Commit → Push → GitHub Actions → VPS
```

Solo se permite modificar el archivo `.env` directamente en el VPS (configuración de producción).

---

## 🛡️ Protecciones Instaladas en el VPS

### 1. Pre-commit Hook
- **Ubicación:** `/opt/splynx-tickets/.git/hooks/pre-commit`
- **Función:** Bloquea commits directos en el VPS
- **Permitido:** Solo `.env`, logs, y backups

### 2. Monitor Automático
- **Script:** `/opt/splynx-tickets/monitor_vps.sh`
- **Cron:** Ejecuta cada hora
- **Función:** Detecta cambios no autorizados y crea alertas

---

## 🔧 Scripts Locales

### 1. Verificar Estado del VPS

```bash
./check_vps_status.sh
```

**Muestra:**
- ✅ Estado del repositorio Git
- 🐳 Estado de contenedores Docker
- 🏥 Health check de la aplicación
- 📋 Últimos logs
- ⚠️ Alertas de cambios no autorizados

**Ejemplo de output:**
```
╔════════════════════════════════════════════════════════════════╗
║        Verificación de Estado del VPS - App Splynx            ║
╚════════════════════════════════════════════════════════════════╝

📊 Estado del Proyecto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Git Status:
✅ Sin cambios - Repositorio limpio

🌿 Branch: main
📝 Último commit: 83930f5 - docs: add executive summary (2 hours ago)

🐳 Estado de Contenedores:
NAME               STATUS          PORTS
splynx-backend     Up 2 hours      0.0.0.0:5605->7842/tcp

🏥 Health Check:
✅ Aplicación respondiendo correctamente
```

---

### 2. Sincronizar .env desde VPS

```bash
./sync_env_from_vps.sh
```

**Función:**
- Descarga el archivo `.env` desde el VPS
- Crea backup del `.env` local actual
- Muestra diferencias entre local y VPS
- Solicita confirmación antes de reemplazar

**Uso:**
```bash
# Sincronizar .env desde producción
./sync_env_from_vps.sh

# Output:
╔════════════════════════════════════════════════════════════════╗
║      Sincronizar .env desde VPS a Local                       ║
╚════════════════════════════════════════════════════════════════╝

✅ Backup creado: .env.backup.20260208_024500
📥 Descargando .env desde VPS...
✅ .env descargado desde VPS

📋 Diferencias entre local y VPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- SECRET_KEY=dev-key
+ SECRET_KEY=production-strong-key-xyz
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¿Reemplazar .env local con la versión del VPS? (y/n):
```

---

## 🚨 Escenarios y Respuestas

### Escenario 1: Cambios no autorizados detectados

**Síntomas:**
- Script de monitoreo crea archivo `ALERT_CAMBIOS.txt` en el VPS
- `./check_vps_status.sh` muestra alerta roja

**Solución:**
```bash
# 1. Conectar al VPS
ssh root@190.7.234.37
cd /opt/splynx-tickets

# 2. Ver qué cambió
git status
git diff

# 3. Revertir cambios no autorizados
git checkout .
git clean -fd

# 4. Verificar
git status  # Debe estar limpio

# 5. Si los cambios eran necesarios, hacerlos localmente:
exit  # Salir del VPS

# En local:
# - Hacer los cambios necesarios
# - git add, git commit, git push
# - GitHub Actions desplegará automáticamente
```

---

### Escenario 2: Necesito modificar .env en producción

**Permitido:** Modificar `.env` directamente en el VPS

```bash
# 1. Conectar al VPS
ssh root@190.7.234.37
cd /opt/splynx-tickets

# 2. Editar .env
nano .env

# 3. Guardar y reiniciar contenedores
docker compose down
docker compose up -d

# 4. Verificar logs
docker compose logs -f backend

# 5. Sincronizar .env a local (opcional)
exit  # Salir del VPS

# En local:
./sync_env_from_vps.sh
```

---

### Escenario 3: Deployment normal

**Flujo correcto:**

```bash
# 1. En local: Hacer cambios
cd /Users/rhernandezba/Downloads/Ipnext/app_splynx
# ... editar archivos ...

# 2. Commit y push
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main

# 3. GitHub Actions despliega automáticamente
# Ver: https://github.com/rhernandezbas/splynx-tickets/actions

# 4. Verificar deployment
./check_vps_status.sh

# 5. Verificar aplicación
curl http://190.7.234.37:5605/health
```

---

### Escenario 4: Rollback de emergencia

**Si algo sale mal después de un deployment:**

```bash
# 1. Conectar al VPS
ssh root@190.7.234.37
cd /opt/splynx-tickets

# 2. Ver últimos commits
git log --oneline -5

# 3. Hacer rollback al commit anterior
git reset --hard <commit-anterior>

# 4. Rebuild de contenedores
docker compose down
docker compose up -d --build

# 5. Verificar
docker compose logs -f backend
```

---

## 📊 Monitoreo Continuo

### Verificación Manual en VPS

```bash
ssh root@190.7.234.37
cd /opt/splynx-tickets

# Ejecutar monitor manualmente
./monitor_vps.sh

# Ver logs del monitor
tail -50 vps_monitor.log

# Ver alertas activas
cat ALERT_CAMBIOS.txt 2>/dev/null
```

### Verificación Automática

El cron job ejecuta el monitor cada hora:
```bash
# Ver configuración de cron
ssh root@190.7.234.37 "crontab -l"

# Output:
# 0 * * * * /opt/splynx-tickets/monitor_vps.sh >> /opt/splynx-tickets/vps_monitor.log 2>&1
```

---

## 🔐 Permisos y Seguridad

### Archivos Críticos

| Archivo | Permisos | Permitido Modificar |
|---------|----------|-------------------|
| `.env` | 600 (rw-------) | ✅ Sí (en VPS) |
| `.git/hooks/pre-commit` | 755 (rwxr-xr-x) | ❌ No |
| `*.py`, `*.sh` | 644/755 | ❌ No (solo local) |
| Logs (`*.log`) | 644 | ✅ Sí (automático) |
| Backups (`*.tar.gz`) | 644 | ✅ Sí (automático) |

---

## 📋 Checklist de Seguridad

### Verificación Diaria

- [ ] Ejecutar `./check_vps_status.sh`
- [ ] Verificar que no hay alertas activas
- [ ] Verificar que contenedores están running
- [ ] Verificar health check OK

### Verificación Semanal

- [ ] Revisar logs de monitor: `ssh root@190.7.234.37 "tail -100 /opt/splynx-tickets/vps_monitor.log"`
- [ ] Verificar backups existen
- [ ] Sincronizar `.env` si hubo cambios

### Verificación Mensual

- [ ] Revisar permisos de archivos críticos
- [ ] Verificar que cron job está activo
- [ ] Revisar disk usage
- [ ] Actualizar documentación si hay cambios

---

## 🆘 Troubleshooting

### El pre-commit hook no funciona

```bash
ssh root@190.7.234.37
cd /opt/splynx-tickets
chmod +x .git/hooks/pre-commit
cat .git/hooks/pre-commit  # Verificar contenido
```

### El cron job no ejecuta

```bash
ssh root@190.7.234.37
crontab -l  # Ver cron jobs
tail -50 /opt/splynx-tickets/vps_monitor.log  # Ver logs
./monitor_vps.sh  # Ejecutar manualmente
```

### sync_env_from_vps.sh falla

```bash
# Verificar conexión SSH
ssh root@190.7.234.37 "echo OK"

# Verificar que .env existe en VPS
ssh root@190.7.234.37 "ls -l /opt/splynx-tickets/.env"

# Descargar manualmente
scp root@190.7.234.37:/opt/splynx-tickets/.env .env.vps
```

---

## 📞 Comandos Rápidos

```bash
# Verificar estado completo
./check_vps_status.sh

# Sincronizar .env desde VPS
./sync_env_from_vps.sh

# Conectar al VPS
ssh root@190.7.234.37

# Ver logs del backend
ssh root@190.7.234.37 "cd /opt/splynx-tickets && docker compose logs -f backend"

# Revertir cambios no autorizados
ssh root@190.7.234.37 "cd /opt/splynx-tickets && git checkout . && git status"

# Reiniciar contenedores
ssh root@190.7.234.37 "cd /opt/splynx-tickets && docker compose restart"
```

---

## 🎉 Resumen

### ✅ Configuración Completada

- [x] Pre-commit hook instalado en VPS
- [x] Script de monitoreo configurado
- [x] Cron job para monitoreo automático
- [x] Script local de verificación
- [x] Script local de sincronización .env
- [x] Documentación completa

### 📐 Flujo de Trabajo

```
┌─────────────┐
│   LOCAL     │
│  (Editar)   │
└──────┬──────┘
       │ git commit, push
       ▼
┌─────────────┐
│   GitHub    │
│ (Repository)│
└──────┬──────┘
       │ GitHub Actions
       ▼
┌─────────────┐
│     VPS     │
│ (Production)│
└─────────────┘
       │
       ▼ Solo .env
┌─────────────┐
│sync_env_from│
│   _vps.sh   │
└─────────────┘
```

---

**Última actualización:** 2026-02-08
**Configurado por:** Claude Sonnet 4.5
