# 🚀 DEPLOYMENT EN PRODUCCIÓN

Guía completa para desplegar "Código de Red" en servidor de producción.

---

## 📋 Pre-requisitos

- Servidor Linux (Ubuntu 20.04+ recomendado)
- Docker + Docker Compose instalados
- Puertos abiertos: 8001 (API), 5173 (Frontend), 9000 (MinIO)
- IP pública del servidor: `31.97.210.250` (ejemplo)

---

## 🔧 PASO 1: Configuración del Servidor

### 1.1 Instalar Docker (si no está instalado)

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalación
docker --version
docker-compose --version
```

### 1.2 Configurar Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8001/tcp  # API
sudo ufw allow 5173/tcp  # Frontend
sudo ufw allow 9000/tcp  # MinIO
sudo ufw enable

# Verificar
sudo ufw status
```

---

## 🔐 PASO 2: Configuración de Variables de Entorno

### 2.1 Copiar archivo de producción

```bash
cd /path/to/CODIGO_DE_RED
cp .env.production.example .env
```

### 2.2 Editar .env con valores de producción

**CRÍTICO**: Cambiar los siguientes valores:

```bash
nano .env
```

```bash
# 1. ENVIRONMENT (OBLIGATORIO)
ENVIRONMENT=production  # NO dejar en development

# 2. CORS - Agregar IP del servidor
CORS_ORIGINS=http://31.97.210.250:5173,http://localhost:5173
FRONTEND_URL=http://31.97.210.250:5173

# 3. FRONTEND - Apuntar al servidor
VITE_API_BASE_URL=http://31.97.210.250:8001

# 4. MINIO - URL externa para presigned URLs
MINIO_EXTERNAL_ENDPOINT=31.97.210.250:9000

# 5. PASSWORDS/SECRETS (CAMBIAR TODOS)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
MINIO_SECRET_KEY=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)

# 6. API RELOAD
API_RELOAD=false  # IMPORTANTE: false en producción

# 7. LOG LEVEL
LOG_LEVEL=INFO  # No usar DEBUG en producción
```

### 2.3 Generar secrets seguros

```bash
# Generar SECRET_KEY para JWT
openssl rand -hex 32

# Generar passwords seguros
openssl rand -base64 32
```

---

## 🚀 PASO 3: Despliegue

### 3.1 Construir y levantar servicios

```bash
cd /path/to/CODIGO_DE_RED

# Construir imágenes (primera vez o después de cambios)
docker-compose build

# Levantar todos los servicios
docker-compose up -d

# Verificar que todo está corriendo
docker-compose ps
```

**Resultado esperado**:
```
NAME                     STATUS
codigo_red_api           Up (healthy)
codigo_red_postgres      Up (healthy)
codigo_red_redis         Up (healthy)
codigo_red_minio         Up (healthy)
codigo_red_frontend      Up
codigo_red_celery_worker Up
codigo_red_celery_beat   Up
```

### 3.2 Ejecutar migraciones

```bash
# Ejecutar migraciones de base de datos
docker-compose exec api alembic upgrade head

# Verificar estado
docker-compose exec api alembic current
```

### 3.3 Cargar datos iniciales

```bash
# Seed de módulos, usuarios, roles
docker-compose exec api python scripts/seed.py

# Seed de compliance (Tabla 1.1.A)
docker-compose exec api python scripts/seed_compliance.py
```

---

## ✅ PASO 4: Verificación

### 4.1 Test de conectividad

```bash
# Test desde el mismo servidor
curl http://localhost:8001/docs
curl http://localhost:5173

# Test desde tu máquina local (reemplazar con IP real)
curl http://31.97.210.250:8001/docs
curl http://31.97.210.250:5173
```

### 4.2 Test de CORS

```bash
# Ejecutar script de validación
./backend/scripts/test_cors.sh 31.97.210.250

# Test manual
curl -I \
  -H "Origin: http://31.97.210.250:5173" \
  -H "Access-Control-Request-Method: GET" \
  http://31.97.210.250:8001/api/v1/auth/me
```

**Resultado esperado**:
```
Access-Control-Allow-Origin: http://31.97.210.250:5173
Access-Control-Allow-Credentials: true
```

### 4.3 Test de autenticación

```bash
# Login
curl -X POST http://31.97.210.250:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@tenant-demo.com",
    "password": "Admin123!"
  }'
```

### 4.4 Acceder desde navegador

1. Abrir navegador en tu máquina local
2. Ir a: `http://31.97.210.250:5173`
3. Login con: `admin@tenant-demo.com` / `Admin123!`

---

## 🔍 PASO 5: Troubleshooting

### Problema: "Cannot connect to API"

**Diagnóstico**:
```bash
# ¿Contenedores corriendo?
docker-compose ps

# ¿Puerto escuchando?
docker-compose exec api netstat -tuln | grep 8000

# ¿Firewall bloqueando?
sudo ufw status
```

**Solución**:
```bash
# Revisar logs
docker-compose logs api --tail=100

# Reiniciar servicios
docker-compose restart api

# Verificar .env
docker-compose exec api printenv | grep -E 'CORS|ENVIRONMENT'
```

### Problema: "CORS error in browser"

**Diagnóstico**:
```bash
# Verificar CORS configurado
./backend/scripts/test_cors.sh 31.97.210.250

# Ver logs del API
docker-compose logs api | grep CORS
```

**Solución**:
```bash
# Editar .env
nano .env

# Cambiar:
ENVIRONMENT=production
CORS_ORIGINS=http://31.97.210.250:5173,http://localhost:5173
FRONTEND_URL=http://31.97.210.250:5173

# Reiniciar
docker-compose restart api

# Verificar en logs
docker-compose logs api | grep "CORS:"
```

### Problema: "Frontend shows 'Network Error'"

**Diagnóstico**:
```bash
# ¿Frontend apuntando al servidor correcto?
docker-compose exec frontend printenv | grep VITE_API_BASE_URL
```

**Solución**:
```bash
# Editar .env
VITE_API_BASE_URL=http://31.97.210.250:8001

# Rebuild frontend
docker-compose up -d --build frontend
```

### Problema: "MinIO presigned URLs fail"

**Diagnóstico**:
```bash
# Verificar MINIO_EXTERNAL_ENDPOINT
docker-compose exec api printenv MINIO_EXTERNAL_ENDPOINT
```

**Solución**:
```bash
# Editar .env
MINIO_EXTERNAL_ENDPOINT=31.97.210.250:9000

# Reiniciar API
docker-compose restart api
```

---

## 📊 PASO 6: Monitoreo

### 6.1 Ver logs en tiempo real

```bash
# Todos los servicios
docker-compose logs -f

# Solo API
docker-compose logs -f api

# Solo errores
docker-compose logs api | grep ERROR
```

### 6.2 Estado de los servicios

```bash
# Resumen
docker-compose ps

# Uso de recursos
docker stats

# Espacio en disco
docker system df
```

### 6.3 Healthchecks

```bash
# API
curl http://localhost:8001/health

# Database
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping
```

---

## 🔒 PASO 7: Seguridad en Producción

### 7.1 Checklist de seguridad

- [ ] `ENVIRONMENT=production` en .env
- [ ] Todos los passwords/secrets cambiados
- [ ] `API_RELOAD=false`
- [ ] CORS configurado con orígenes específicos
- [ ] Firewall configurado
- [ ] SSL/HTTPS configurado (recomendado)
- [ ] Backups automáticos de PostgreSQL
- [ ] Logs rotativos configurados
- [ ] Rate limiting activo
- [ ] Sentry configurado (opcional)

### 7.2 Configurar HTTPS (Recomendado)

```bash
# Instalar Nginx
sudo apt install nginx certbot python3-certbot-nginx

# Configurar proxy reverse
sudo nano /etc/nginx/sites-available/codigo-red

# Contenido:
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/codigo-red /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Obtener certificado SSL
sudo certbot --nginx -d yourdomain.com
```

### 7.3 Backups automáticos

```bash
# Crear script de backup
cat > backup-postgres.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U codigo_red_user codigo_red_db | gzip > backup_$DATE.sql.gz
# Mantener solo últimos 7 días
find . -name "backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup-postgres.sh

# Agregar a crontab (diario a las 2 AM)
crontab -e
# Agregar:
0 2 * * * /path/to/backup-postgres.sh
```

---

## 🔄 PASO 8: Updates y Mantenimiento

### 8.1 Actualizar código

```bash
# Pull cambios
git pull origin main

# Rebuild y restart
docker-compose up -d --build

# Ejecutar migraciones nuevas
docker-compose exec api alembic upgrade head
```

### 8.2 Reiniciar servicios

```bash
# Reiniciar todo
docker-compose restart

# Reiniciar servicio específico
docker-compose restart api

# Rebuild completo
docker-compose down
docker-compose up -d --build
```

### 8.3 Limpieza

```bash
# Limpiar imágenes antiguas
docker system prune -a

# Ver espacio usado
docker system df
```

---

## 📞 Soporte

Si tienes problemas:

1. Revisar logs: `docker-compose logs api`
2. Ejecutar test de CORS: `./backend/scripts/test_cors.sh`
3. Verificar .env: `cat .env | grep -E 'CORS|ENVIRONMENT|FRONTEND'`
4. Revisar documentación: `backend/docs/`

---

**Última actualización**: 26 de Febrero de 2026
