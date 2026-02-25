# ==================================================
# Dockerfile para Backend (FastAPI + Celery)
# Multi-stage build para optimizar imagen
# ==================================================

FROM python:3.12-slim as base

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# Stage: dependencies
# ==================================================
FROM base as dependencies

# Copiar archivos de dependencias
COPY pyproject.toml ./

# Instalar Poetry y dependencias
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# ==================================================
# Stage: development
# ==================================================
FROM dependencies as development

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando por defecto (puede ser sobreescrito en docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==================================================
# Stage: production
# ==================================================
FROM dependencies as production

# Copiar código fuente
COPY . .

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Comando para producción (con gunicorn + uvicorn workers)
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
