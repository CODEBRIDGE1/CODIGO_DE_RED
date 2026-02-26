# 🚀 ACTUALIZAR SERVIDOR DE PRODUCCIÓN

Guía para actualizar el servidor **31.97.210.250** con los últimos cambios.

---

## 📋 Pre-requisitos

Asegúrate de tener:
- Acceso SSH al servidor: `ssh root@31.97.210.250`
- Git configurado en el servidor
- Docker y Docker Compose instalados

---

## 🔄 PASOS PARA ACTUALIZAR

### 1️⃣ Conectar al servidor

```bash
ssh root@31.97.210.250
```

### 2️⃣ Ir al directorio del proyecto

```bash
cd /ruta/del/proyecto/CODIGO_DE_RED
# O la ruta donde tengas clonado el repositorio
```

### 3️⃣ Hacer backup de la base de datos (IMPORTANTE)

```bash
# Backup rápido de PostgreSQL
docker-compose exec -T postgres pg_dump -U codigo_red_user codigo_red_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Verificar que se creó el backup
ls -lh backup_*.sql
```

### 4️⃣ Traer los últimos cambios del repositorio

```bash
# Ver cambios remotos
git fetch origin

# Ver diferencias
git log HEAD..origin/main --oneline

# Aplicar cambios
git pull origin main
```

**Salida esperada**:
```
Updating 1e22568..22e834f
Fast-forward
 32 files changed, 2712 insertions(+), 461 deletions(-)
 create mode 100644 .env.production.example
 create mode 100644 DEPLOYMENT.md
 ...
```

### 5️⃣ Actualizar variables de entorno

```bash
# Opción A: Si NO tienes .env configurado
cp .env.production.example .env
nano .env  # Editar con tus valores

# Opción B: Si YA tienes .env, agregar nuevas variables
# Revisar .env.production.example y agregar lo que falte
nano .env
```

**Variables críticas a configurar**:
```bash
# Cambiar de development a production
ENVIRONMENT=production

# CORS - Agregar IP del servidor
CORS_ORIGINS=http://31.97.210.250:5173,http://localhost:5173
FRONTEND_URL=http://31.97.210.250:5173

# Frontend - URL del API
VITE_API_BASE_URL=http://31.97.210.250:8001

# MinIO - URL externa
MINIO_EXTERNAL_ENDPOINT=31.97.210.250:9000

# Cambiar TODOS los passwords y secrets (OBLIGATORIO)
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
MINIO_SECRET_KEY=$(openssl rand -base64 32)

# Reload en false para producción
API_RELOAD=false
```

### 6️⃣ Detener contenedores actuales

```bash
# Ver contenedores corriendo
docker-compose ps

# Detener todo (mantiene volúmenes/datos)
docker-compose down
```

**⚠️ NO usar `docker-compose down -v` porque borra la base de datos**

### 7️⃣ Rebuildar imágenes con nuevos cambios

```bash
# Rebuildar todas las imágenes
docker-compose build --no-cache

# O rebuildar solo las que cambiaron
docker-compose build api frontend
```

### 8️⃣ Levantar servicios actualizados

```bash
# Levantar en modo detached
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f
```

**Salida esperada**:
```
✔ Container codigo_red_postgres  Started
✔ Container codigo_red_redis     Started
✔ Container codigo_red_minio     Started
✔ Container codigo_red_api       Started
✔ Container codigo_red_frontend  Started
✔ Container codigo_red_celery_worker Started
✔ Container codigo_red_celery_beat Started
```

### 9️⃣ Ejecutar migraciones nuevas

```bash
# Ver estado de migraciones
docker-compose exec api alembic current

# Aplicar migraciones pendientes
docker-compose exec api alembic upgrade head

# Verificar que se aplicaron correctamente
docker-compose exec api alembic current
```

**Salida esperada**:
```
INFO  [alembic.runtime.migration] Running upgrade 359d44c42b9d -> 240a1b9b943a, create_projects_tables
240a1b9b943a (head)
```

### 🔟 Verificar que todo funciona

```bash
# 1. Verificar estado de contenedores
docker-compose ps
# Todos deben estar "Up (healthy)" o "Up"

# 2. Verificar logs del API (últimas 20 líneas)
docker-compose logs api --tail=20

# 3. Test de CORS
./backend/scripts/test_cors.sh 31.97.210.250 8001

# 4. Test de conectividad
curl http://localhost:8001/docs
curl http://localhost:5173

# 5. Desde tu máquina local
curl http://31.97.210.250:8001/docs
# Debe devolver HTML de Swagger UI
```

---

## ✅ VALIDACIÓN COMPLETA

Después de actualizar, valida que todo funciona:

### Desde el servidor:

```bash
# API Health
curl http://localhost:8001/health

# Base de datos
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping
```

### Desde tu navegador (máquina local):

1. **Frontend**: http://31.97.210.250:5173
   - Login debe funcionar
   
2. **API Docs**: http://31.97.210.250:8001/docs
   - Swagger debe cargar

3. **Prueba funcional**:
   - Login con: `admin@tenant-demo.com` / `Admin123!`
   - Ver módulo "Empresas"
   - Ver módulo "Obligaciones"
   - Crear un proyecto
   - Subir una evidencia

---

## 🔧 TROUBLESHOOTING

### Problema: "Cannot connect to API"

```bash
# Ver logs del API
docker-compose logs api --tail=50

# Verificar que el API está escuchando
docker-compose exec api netstat -tuln | grep 8000

# Verificar firewall
sudo ufw status
```

### Problema: "CORS error"

```bash
# Verificar variables de entorno en el contenedor
docker-compose exec api printenv | grep CORS

# Debe mostrar:
# CORS_ORIGINS=http://31.97.210.250:5173,http://localhost:5173
# FRONTEND_URL=http://31.97.210.250:5173

# Si no, editar .env y reiniciar
nano .env
docker-compose restart api
```

### Problema: "Migration failed"

```bash
# Ver migraciones aplicadas
docker-compose exec api alembic history

# Ver estado actual
docker-compose exec api alembic current

# Si hay error, ver detalles
docker-compose logs api | grep -i error

# Rollback de emergencia (solo si es necesario)
docker-compose exec api alembic downgrade -1
```

### Problema: "Frontend shows blank page"

```bash
# Verificar que VITE_API_BASE_URL es correcto
docker-compose exec frontend printenv | grep VITE

# Debe mostrar:
# VITE_API_BASE_URL=http://31.97.210.250:8001

# Si no, editar .env y rebuild
nano .env
docker-compose up -d --build frontend
```

### Problema: "Database connection error"

```bash
# Verificar PostgreSQL
docker-compose exec postgres psql -U codigo_red_user -d codigo_red_db -c "SELECT 1"

# Ver logs de PostgreSQL
docker-compose logs postgres --tail=30

# Verificar password en .env coincide con el del contenedor
```

---

## 🔄 ROLLBACK (Si algo sale mal)

Si necesitas volver a la versión anterior:

```bash
# 1. Detener contenedores
docker-compose down

# 2. Volver al commit anterior
git log --oneline -5  # Ver últimos commits
git checkout 1e22568  # Reemplazar con el hash anterior

# 3. Restaurar backup de base de datos
docker-compose up -d postgres
cat backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T postgres psql -U codigo_red_user -d codigo_red_db

# 4. Levantar todo
docker-compose up -d
```

---

## 📊 VERIFICACIÓN POST-UPDATE

Lista de verificación después de actualizar:

- [ ] Todos los contenedores en estado "Up"
- [ ] API responde en http://31.97.210.250:8001/docs
- [ ] Frontend carga en http://31.97.210.250:5173
- [ ] Login funciona correctamente
- [ ] Módulo "Empresas" muestra datos
- [ ] Módulo "Obligaciones" permite clasificar
- [ ] Módulo "Proyectos" permite crear proyectos
- [ ] Se pueden subir evidencias
- [ ] Se pueden eliminar evidencias
- [ ] CORS funciona desde el navegador
- [ ] No hay errores en logs: `docker-compose logs --tail=50`

---

## 📝 NOTAS IMPORTANTES

1. **Siempre hacer backup antes de actualizar**
2. **No usar `-v` en `docker-compose down` (borra datos)**
3. **Cambiar passwords en producción** (no usar los del ejemplo)
4. **Verificar firewall** permite puertos 8001, 5173, 9000
5. **Monitorear logs** después de actualizar: `docker-compose logs -f`

---

## 🆘 CONTACTO DE EMERGENCIA

Si algo no funciona después de seguir estas instrucciones:

1. **No apagues el servidor**
2. **Captura los logs**: `docker-compose logs > error_logs.txt`
3. **Captura el estado**: `docker-compose ps > status.txt`
4. **Revisa**: [DEPLOYMENT.md](DEPLOYMENT.md) para troubleshooting detallado

---

**Última actualización**: 26 de Febrero de 2026  
**Commit aplicado**: `22e834f` - CORS hardening, migration fixes, projects completion
