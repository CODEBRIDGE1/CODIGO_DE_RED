# 🚀 Plataforma Código de Red - Instrucciones de Acceso

## ✅ Servicios Levantados

La plataforma ya está corriendo con los siguientes servicios:

### Puertos Configurados
```
Frontend:    http://localhost:5173
API:         http://localhost:8001
API Docs:    http://localhost:8001/docs
PostgreSQL:  localhost:5433
Redis:       localhost:6380
MinIO:       http://localhost:9000 (Console: http://localhost:9001)
```

> **Nota**: Los puertos se modificaron para evitar conflictos con otros proyectos Docker.

---

## 📋 Verificar Estado de los Servicios

```bash
docker-compose ps
```

Deberías ver 7 containers corriendo:
- ✅ codigo_red_postgres (healthy)
- ✅ codigo_red_redis (healthy)
- ✅ codigo_red_minio (healthy)
- ✅ codigo_red_api (up)
- ✅ codigo_red_celery_worker (up)
- ✅ codigo_red_celery_beat (up)
- ✅ codigo_red_frontend (up)

---

## 🔐 Credenciales de Acceso

### Superadmin (sin tenant)
- **Email**: `superadmin@codebridge.com`
- **Password**: `SuperAdmin123!`

### Administrador del Tenant Demo
- **Email**: `admin@tenant-demo.com`
- **Password**: `Admin123!`
- **Tenant**: `tenant-demo`

### MinIO (Almacenamiento S3)
- **Access Key**: `minioadmin`
- **Secret Key**: `minioadmin_secret_change_me`

---

## 📊 Base de Datos

### Datos Iniciales Creados (Seed)
- ✅ 8 módulos (Dashboard, Empresas, Obligaciones, Proyectos, Evidencias, Cotizaciones, Usuarios, Bitácora)
- ✅ 36 permisos (5 acciones x 7 módulos + Dashboard)
- ✅ 1 tenant demo (`tenant-demo`)
- ✅ 1 licencia (50 usuarios, 100GB, válida 1 año)
- ✅ 1 rol Admin con todos los permisos
- ✅ 2 usuarios (superadmin + admin demo)

### Verificar Conexión a PostgreSQL
```bash
# Dentro del container API
docker-compose exec api python -c "
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
import asyncio

async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text('SELECT COUNT(*) FROM users'))
        count = result.scalar()
        print(f'✓ Usuarios en DB: {count}')

asyncio.run(test())
"
```

---

## 🧪 Probar API

### Health Check
```bash
curl http://localhost:8001/health
```

### OpenAPI Schema
```bash
curl http://localhost:8001/openapi.json | jq '.info'
```

### Documentación Interactiva
Abre tu navegador en: **http://localhost:8001/docs**

---

## 🛠️ Comandos Útiles

### Ver Logs
```bash
# Todos los servicios
docker-compose logs -f

# Solo API
docker-compose logs -f api

# Solo Frontend
docker-compose logs -f frontend
```

### Reiniciar Servicios
```bash
# Reiniciar solo API
docker-compose restart api

# Reiniciar todo
docker-compose restart
```

### Entrar al Container API
```bash
docker-compose exec api bash
```

### Ejecutar Migraciones
```bash
# Crear nueva migración
docker-compose exec api alembic revision --autogenerate -m "nombre_de_migracion"

# Aplicar migraciones pendientes
docker-compose exec api alembic upgrade head

# Rollback última migración
docker-compose exec api alembic downgrade -1
```

### Re-ejecutar Seed (⚠️ Cuidado: duplicará datos)
```bash
docker-compose exec api python scripts/seed.py
```

---

## 🌐 Acceso Frontend

### Desarrollo Local
Abre: **http://localhost:5173**

El frontend actualmente muestra un placeholder Svelte 5 con:
- Contador de ejemplo
- Link a la documentación API
- Estilos Tailwind CSS

### Configurar Variables de Entorno Frontend
El frontend lee las siguientes variables del archivo `.env`:

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_APP_NAME="Código de Red Platform"
```

---

## 🔥 Detener Todo

```bash
# Detener sin eliminar volúmenes
docker-compose down

# Detener y eliminar volúmenes (⚠️ borra la base de datos)
docker-compose down -v
```

---

## 📦 Stack Tecnológico Implementado

### Backend
- ✅ **FastAPI** 0.115.12 (async)
- ✅ **SQLAlchemy** 2.0+ (async con asyncpg)
- ✅ **Pydantic** v2 (validation + settings)
- ✅ **Alembic** (migraciones)
- ✅ **Celery** (tareas asíncronas)
- ✅ **Argon2** (hashing passwords)
- ✅ **PyJWT** (autenticación JWT)
- ✅ **SlowAPI** (rate limiting)

### Frontend
- ✅ **Svelte 5** (runes + reactive)
- ✅ **TypeScript** 5.7
- ✅ **Vite** 5.4
- ✅ **Tailwind CSS** 3.4

### Infraestructura
- ✅ **PostgreSQL 15** (alpine)
- ✅ **Redis 7** (alpine)
- ✅ **MinIO** (S3-compatible storage)
- ✅ **Docker Compose** (orchestration)
- ✅ **Nginx** (reverse proxy - configurado pero no usado aún)

---

## ✨ Arquitectura Implementada

### Multi-Tenancy
- Estrategia: **Shared Database** con `tenant_id`
- Filtrado automático con `TenantContext`
- Subdominios: `{tenant}.codebridge.com`

### Seguridad
- Password hashing: **Argon2id** (time_cost=2, memory_cost=65536)
- JWT: Access token (15min) + Refresh token (7 días)
- CORS: Configurado para localhost:5173 y localhost:3000
- Rate Limiting: 100 req/min por IP

### RBAC (Roles & Permissions)
- Permisos granulares: `read`, `create`, `update`, `delete`, `export`
- Roles asignables por tenant
- Middleware `PermissionChecker` para endpoints

### Auditoría
- Logs de todas las acciones CRUD
- Tabla `audit_logs` con:
  - Usuario, Tenant, Módulo, Acción
  - Request ID (tracking)
  - IP, User-Agent
  - Payload (antes/después)

---

## 🚧 Pendiente de Implementar

### API Endpoints
- [ ] `/api/v1/auth/login` - Login
- [ ] `/api/v1/auth/refresh` - Refresh token
- [ ] `/api/v1/auth/me` - Usuario actual
- [ ] `/api/v1/companies` - CRUD Empresas
- [ ] `/api/v1/obligations` - CRUD Obligaciones
- [ ] `/api/v1/projects` - CRUD Proyectos
- [ ] `/api/v1/evidences` - CRUD Evidencias
- [ ] `/api/v1/quotes` - CRUD Cotizaciones
- [ ] `/api/v1/users` - CRUD Usuarios
- [ ] `/api/v1/audit` - Logs de auditoría

### Frontend
- [ ] Rutas (SvelteKit o Svelte Router)
- [ ] Login Page
- [ ] Dashboard
- [ ] Módulos CRUD
- [ ] Gestión de permisos UI
- [ ] Upload de archivos a MinIO

### Infraestructura
- [ ] Configurar Nginx para servir frontend + API
- [ ] SSL/TLS certificates
- [ ] CI/CD pipeline
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Backup automático de PostgreSQL

---

## 📝 Logs y Debugging

### Ver logs del API en tiempo real
```bash
docker-compose logs -f api
```

### Ver errores de Celery
```bash
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### Conectar a PostgreSQL directamente
```bash
# Desde tu máquina
psql -h localhost -p 5433 -U codigo_red_user -d codigo_red_db

# Password: super_secret_password_change_me
```

### Ver estado de Redis
```bash
docker-compose exec redis redis-cli
> ping
PONG
> keys *
```

---

## 🎯 Próximos Pasos

1. **Implementar Login Endpoint** (`POST /api/v1/auth/login`)
2. **Crear componentes de autenticación en frontend**
3. **Implementar CRUD de Empresas** (backend + frontend)
4. **Configurar upload de archivos a MinIO**
5. **Crear tests unitarios con pytest**
6. **Dockerizar para producción** (multi-stage builds optimizados)

---

## 📚 Documentación Completa

- **README.md**: Arquitectura completa y contratos API
- **CODIGO_COMPLETO.md**: Patrones de código y ejemplos
- Este archivo: Instrucciones de acceso y operación

---

**¡La plataforma está lista para desarrollar las funcionalidades faltantes!** 🚀
