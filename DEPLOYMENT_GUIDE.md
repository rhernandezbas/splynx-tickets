# 🚀 Guía de Deployment - Panel de Administración

## Arquitectura

```
Internet → VPS:7842 → Nginx (Frontend) → Backend:7842
                         ↓
                    React App (estático)
```

## ✅ Archivos Creados

1. **`frontend/Dockerfile`** - Build multi-stage del frontend
2. **`frontend/nginx.conf`** - Configuración nginx con proxy
3. **`frontend/.dockerignore`** - Archivos a ignorar
4. **`docker-compose.yml`** - Actualizado con frontend + backend

## 🔄 Deployment Automático

### Cada push a `main`:
1. GitHub Actions se conecta al VPS
2. Actualiza el código
3. Construye imágenes Docker
4. Reinicia contenedores
5. Verifica que estén corriendo

### URL de Acceso:
```
http://190.7.234.37:7842
```

## 🛠️ Comandos en el VPS

### Ver estado
```bash
ssh root@190.7.234.37
cd /opt/splynx-tickets
docker compose ps
```

### Ver logs
```bash
docker compose logs -f frontend
docker compose logs -f backend
```

### Reiniciar
```bash
docker compose restart
```

## 📝 Notas Importantes

- **Puerto 7842**: Expuesto para el frontend (nginx)
- **Backend**: Solo accesible internamente en red Docker
- **Proxy**: Nginx redirige `/api/*` al backend
- **React Router**: Todas las rutas van a `index.html`

## 🚀 Para Deployar

```bash
git add .
git commit -m "Deploy frontend"
git push origin main
```

¡GitHub Actions hace el resto automáticamente!
