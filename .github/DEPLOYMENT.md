# Configuración de Despliegue Automático a VPS

Este repositorio está configurado con GitHub Actions para desplegar automáticamente a tu VPS cada vez que hagas push a la rama `main`.

## 📋 Requisitos Previos en el VPS

1. **Docker y Docker Compose instalados**
2. **Git instalado**
3. **Repositorio clonado en el VPS**
4. **Acceso SSH configurado**

## 🔐 Configurar Secretos en GitHub

Ve a tu repositorio en GitHub: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Agrega los siguientes secretos:

### 1. VPS_HOST
- **Valor**: La IP o dominio de tu VPS
- **Ejemplo**: `192.168.1.100` o `miservidor.com`

### 2. VPS_USERNAME
- **Valor**: Usuario SSH del VPS
- **Ejemplo**: `root` o `ubuntu` o `deploy`

### 3. VPS_SSH_KEY
- **Valor**: Tu clave privada SSH (completa)
- **Cómo obtenerla**:
  ```bash
  cat ~/.ssh/id_rsa
  ```
- **Importante**: Copia TODO el contenido, incluyendo:
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  ...
  -----END OPENSSH PRIVATE KEY-----
  ```

### 4. VPS_PORT
- **Valor**: Puerto SSH del VPS
- **Ejemplo**: `22` (puerto por defecto)

### 5. VPS_PROJECT_PATH
- **Valor**: Ruta completa donde está clonado el proyecto en el VPS
- **Ejemplo**: `/home/deploy/splynx-tickets` o `/opt/app-splynx`

## 🚀 Preparar el VPS

Conéctate a tu VPS y ejecuta:

```bash
# 1. Instalar Docker (si no está instalado)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Instalar Docker Compose (si no está instalado)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Crear directorio para el proyecto
sudo mkdir -p /opt/app-splynx
cd /opt/app-splynx

# 4. Clonar el repositorio
git clone https://github.com/rhernandezbas/splynx-tickets.git .

# 5. Configurar permisos (si es necesario)
sudo chown -R $USER:$USER /opt/app-splynx

# 6. Primera ejecución manual
docker-compose up -d --build
```

## 🔑 Configurar SSH Key en el VPS

Si aún no tienes una clave SSH, créala:

```bash
# En tu máquina local
ssh-keygen -t rsa -b 4096 -C "deploy@splynx-tickets"

# Copiar la clave pública al VPS
ssh-copy-id usuario@tu-vps-ip

# Verificar conexión
ssh usuario@tu-vps-ip
```

## ✅ Verificar Configuración

Una vez configurados todos los secretos:

1. Haz un cambio pequeño en el código
2. Haz commit y push a `main`
3. Ve a GitHub → Actions → Verás el workflow ejecutándose
4. Si todo está bien, verás ✅ en verde

## 🔄 Flujo de Despliegue

Cada vez que hagas `git push` a la rama `main`:

1. GitHub Actions se activa automáticamente
2. Se conecta a tu VPS por SSH
3. Hace `git pull` de los últimos cambios
4. Detiene los contenedores actuales
5. Construye la nueva imagen Docker
6. Levanta los contenedores actualizados
7. Verifica que todo esté funcionando

## 🐛 Troubleshooting

### Error: Permission denied (publickey)
- Verifica que `VPS_SSH_KEY` contenga la clave privada completa
- Asegúrate de que la clave pública esté en `~/.ssh/authorized_keys` del VPS

### Error: docker: command not found
- Docker no está instalado en el VPS
- Ejecuta los comandos de instalación arriba

### Error: Permission denied (docker)
- Agrega tu usuario al grupo docker:
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```

### Ver logs del despliegue
- Ve a GitHub → Actions → Click en el workflow fallido
- Revisa los logs de cada step

## 📱 Despliegue Manual

También puedes activar el despliegue manualmente:

1. Ve a GitHub → Actions
2. Selecciona "Deploy to VPS"
3. Click en "Run workflow"
4. Selecciona la rama `main`
5. Click en "Run workflow"

## 🔒 Seguridad

- ✅ Nunca compartas tus secretos de GitHub
- ✅ Usa claves SSH en lugar de contraseñas
- ✅ Considera usar un usuario dedicado para deploys (no root)
- ✅ Configura un firewall en tu VPS
- ✅ Mantén Docker y el sistema actualizados

## 📊 Monitoreo

Después del despliegue, verifica:

```bash
# En el VPS
cd /opt/app-splynx
docker-compose ps
docker-compose logs -f --tail=100
```

Tu aplicación estará disponible en: `http://tu-vps-ip:7842`
