# Multi-stage build para optimizar el tamaño de la imagen
FROM python:3.10-slim as builder

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmariadb-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Configurar Poetry para no crear entornos virtuales (no necesario en Docker)
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copiar archivos de dependencias
COPY pyproject.toml poetry.lock ./

# Instalar dependencias
RUN poetry install --no-root --no-dev && rm -rf $POETRY_CACHE_DIR

# Etapa final - imagen más ligera
FROM python:3.10-slim

# Instalar dependencias de runtime
RUN apt-get update && apt-get install -y \
    libmariadb3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para ejecutar la aplicación
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copiar las dependencias instaladas desde el builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar el código de la aplicación
COPY --chown=appuser:appuser . .

# Crear directorio de logs con permisos correctos
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# Cambiar al usuario no-root
USER appuser

# Exponer el puerto de la aplicación
EXPOSE 7842

# Variables de entorno por defecto (pueden ser sobrescritas)
ENV FLASK_APP=app \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1

# Healthcheck para verificar que la aplicación está corriendo
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7842/ || exit 1

# Comando para ejecutar la aplicación
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=7842"]
