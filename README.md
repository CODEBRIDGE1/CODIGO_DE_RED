# PLATAFORMA CÓDIGO DE RED (CodeBridge SaaS)
### Jorge Ernesto Herrera Cazares

> ✅ **MIGRATION HARDENING COMPLETADO** (26 Feb 2026)  
> Todas las migraciones de Alembic han sido auditadas y corregidas para garantizar:  
> Zero-downtime deployments | Rollback seguro | PostgreSQL 15 compatible | asyncpg compatible  
> 📄 Ver reporte completo: [backend/docs/MIGRATION_HARDENING_REPORT.md](backend/docs/MIGRATION_HARDENING_REPORT.md)

## 🏗️ Arquitectura

**Plataforma SaaS Multi-tenant** para gestión de cumplimiento del Código de Red con:
- ✅ Multi-tenancy con aislamiento estricto (tenant_id scoping)
- ✅ RBAC granular por módulo/acción
- ✅ Auditoría completa de eventos
- ✅ Autenticación JWT (access + refresh con rotación)
- ✅ Storage S3 (MinIO) con presigned URLs
- ✅ Procesamiento asíncrono (Celery + Redis)
- ✅ UX keyboard-first (atajos globales + por módulo)
- ✅ Responsive mobile + desktop

## 🚀 LEVANTAR EN 3 COMANDOS

```bash
# 1. Clonar variables de entorno
cp .env.example .env

# 2. Levantar toda la infraestructura
docker-compose up -d

# 3. Ejecutar migraciones y seed
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/seed.py
```

**¡Listo!** Accede a:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

## 👤 USUARIOS DE PRUEBA

Después del seed, puedes iniciar sesión con:

### Super Admin (gestión global de tenants)
- Email: `superadmin@codebridge.com`
- Password: `SuperAdmin123!`
- Permisos: Administración global de tenants, licencias, módulos

### Tenant Demo - Admin
- Email: `admin@tenant-demo.com`
- Password: `Admin123!`
- Tenant: `tenant-demo`
- Permisos: Todos los módulos del tenant

### Tenant Demo - Usuario Operativo
- Email: `operador@tenant-demo.com`
- Password: `Operador123!`
- Tenant: `tenant-demo`
- Permisos: Empresas, Obligaciones, Proyectos, Evidencias (sin gestión de usuarios)

## 📁 Stack Tecnológico

### Backend
- **Python 3.12** + FastAPI (async)
- **SQLAlchemy 2** (async) + asyncpg
- **Pydantic v2** para DTOs y validaciones
- **Alembic** para migraciones
- **Celery** + Redis para tareas asíncronas
- **Argon2** para hashing de passwords
- **JWT** para autenticación (PyJWT)

### Frontend
- **Svelte 5** + TypeScript
- **Vite** (build tool)
- **Tailwind CSS** para estilos
- **SvelteKit** para routing

### Infraestructura
- **PostgreSQL** 15
- **Redis** 7 (Celery broker + cache)
- **MinIO** (S3-compatible storage)
- **Nginx** (reverse proxy)
- **Docker** + Docker Compose

## 📂 Estructura del Proyecto

```
codigo-de-red/
├── backend/          # API FastAPI + Celery workers
├── frontend/         # Svelte 5 + TypeScript
├── infra/           # Nginx configs
├── docker-compose.yml
└── .env.example
```

## 🔑 Multi-Tenancy

### Estrategia: Shared Database con tenant_id

Todas las tablas incluyen `tenant_id` (excepto las globales como `tenants`, `modules`).

**Aislamiento:**
- Middleware `TenantContext` extrae tenant de:
  - Header `X-Tenant-ID`
  - Subdominio (ej: `tenant-demo.codigo-red.com`)
- Todas las queries automáticamente filtran por `tenant_id`
- Endpoints verifican permisos del usuario dentro de su tenant

**Prevención de fugas cross-tenant:**
- Scoping automático en queries (SQLAlchemy filters)
- Validaciones en dependencies FastAPI
- Tests de aislamiento en CI

## 🔐 RBAC (Role-Based Access Control)

### Modelo de Permisos

Cada **Rol** tiene múltiples **Permisos**.  
Cada **Permiso** asocia un **Módulo** + **Acción**.

**Acciones disponibles:**
- `read` - Listar y ver detalles
- `create` - Crear nuevos registros
- `update` - Editar existentes
- `delete` - Eliminar
- `approve` - Aprobar flujos
- `export` - Exportar datos (CSV/PDF)
- `import` - Importar masivos
- `manage_users` - Gestionar usuarios/roles del tenant
- `view_audit` - Ver bitácora de auditoría
- `manage_billing` - Gestionar licencias (solo admin)

**Enforcement:**
```python
# Backend (FastAPI dependency)
@router.get("/companies")
async def list_companies(
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(require_permission("companies", "read"))
):
    # Solo ejecuta si user tiene permiso companies.read
    ...
```

## 📊 Módulos Core

1. **Dashboard** - KPIs de cumplimiento, pendientes críticos, alertas
2. **Empresas** - Alta y gestión de expediente empresarial (centros de carga, docs)
3. **Perfilado/Matriz de Obligaciones** - Clasificación automática y matriz de cumplimiento
4. **Proyectos** - Planes de trabajo por obligación (tareas, responsables, avance)
5. **Evidencias** - Expediente electrónico (reportes, fotos, estudios, facturas)
6. **Cotizaciones** - Solicitudes comerciales y propuestas
7. **Usuarios/Roles** - Gestión de usuarios y permisos por tenant
8. **Bitácora** - Auditoría completa con búsqueda y exportación
9. **Admin Global** - Gestión de tenants, licencias, storage quotas (superadmin)

## 🔍 Auditoría / Bitácora

**Middleware automático** que registra:
- Usuario, tenant, módulo, acción, entidad, ID
- IP, user-agent, timestamp
- Before/After (diff resumido para updates)
- Eventos de auth (login, logout, refresh, fail)
- Operaciones con archivos (upload, download, delete)

**Tabla:** `audit_logs`

**Búsqueda por:**
- Usuario, tenant, módulo, acción, fecha, IP
- Exportable a CSV/PDF (con permiso `view_audit`)

## ⌨️ UX Keyboard-First

### Atajos Globales (ALT + tecla)
- `ALT+D` - Dashboard
- `ALT+E` - Empresas
- `ALT+O` - Obligaciones
- `ALT+P` - Proyectos
- `ALT+V` - Evidencias
- `ALT+C` - Cotizaciones
- `ALT+U` - Usuarios
- `ALT+B` - Bitácora

### Atajos por Módulo
- `N` - Nuevo registro
- `E` - Editar seleccionado
- `S` - Guardar
- `X` - Exportar
- `I` - Importar
- `ESC` - Cancelar/Cerrar modal

### Comportamiento
- Focus automático en primer input al entrar a módulo/modal
- Tab order lógico
- Feedback visual de atajos activos
- Command Palette (`CTRL+K`) - próximamente

## 🗄️ Modelo de Datos (Principales Tablas)

### Autenticación y Tenancy
- `tenants` - Clientes de la plataforma
- `licenses` - Licencias por tenant (usuarios, storage, módulos, vigencia)
- `users` - Usuarios por tenant
- `roles` - Roles personalizados por tenant
- `permissions` - Permisos (módulo + acción)
- `role_permissions` - Many-to-many
- `user_roles` - Many-to-many

### Auditoría
- `audit_logs` - Registro completo de eventos

### Módulos Core
- `modules` - Catálogo de módulos del sistema (global)
- `companies` - Empresas (expediente por tenant)
- `obligations` - Catálogo de obligaciones normativas
- `company_obligations` - Matriz de cumplimiento por empresa
- `projects` - Proyectos/planes de trabajo
- `tasks` - Tareas dentro de proyectos
- `evidences` - Archivos y documentos (metadata + MinIO)
- `quotes` - Cotizaciones y propuestas
- `quote_items` - Items/servicios dentro de cotización

**Índices críticos:**
- `tenant_id` en todas las tablas tenant-scoped
- Composite index `(tenant_id, entity_id)` para queries frecuentes
- `email` único por tenant
- Timestamps `created_at`, `updated_at`

## 🔌 Endpoints API Principales

### Auth (`/api/v1/auth`)
- `POST /login` - Login (email, password) → access + refresh tokens
- `POST /refresh` - Renovar access token (con refresh token)
- `POST /logout` - Invalidar refresh token
- `GET /me` - Datos del usuario actual

### Tenants Admin (`/api/v1/admin/tenants`) - Solo superadmin
- `GET /tenants` - Listar tenants
- `POST /tenants` - Crear tenant + licencia inicial
- `GET /tenants/{id}` - Detalle de tenant
- `PUT /tenants/{id}` - Actualizar tenant
- `POST /tenants/{id}/suspend` - Suspender tenant
- `POST /tenants/{id}/activate` - Activar tenant

### Empresas (`/api/v1/companies`)
- `GET /` - Listar empresas del tenant
- `POST /` - Crear empresa (expediente base)
- `GET /{id}` - Detalle empresa + centros de carga
- `PUT /{id}` - Actualizar empresa
- `DELETE /{id}` - Eliminar empresa

### Obligaciones (`/api/v1/obligations`)
- `GET /` - Catálogo de obligaciones
- `GET /companies/{company_id}/matrix` - Matriz de cumplimiento de empresa
- `PUT /companies/{company_id}/obligations/{obl_id}` - Actualizar estado cumplimiento

### Proyectos (`/api/v1/projects`)
- `GET /` - Listar proyectos del tenant
- `POST /` - Crear proyecto
- `GET /{id}` - Detalle proyecto + tareas
- `PUT /{id}` - Actualizar proyecto
- `POST /{id}/tasks` - Crear tarea en proyecto

### Evidencias (`/api/v1/evidences`)
- `POST /upload-url` - Generar presigned URL para upload a MinIO
- `POST /` - Registrar metadata de evidencia (tras upload exitoso)
- `GET /` - Listar evidencias del tenant
- `GET /{id}/download-url` - Presigned URL de descarga

### Cotizaciones (`/api/v1/quotes`)
- `GET /` - Listar cotizaciones
- `POST /` - Crear cotización
- `GET /{id}` - Detalle + items
- `PUT /{id}` - Actualizar cotización

### Usuarios/Roles (`/api/v1/users`, `/api/v1/roles`)
- `GET /users` - Listar usuarios del tenant
- `POST /users` - Crear usuario (validar límite de licencia)
- `PUT /users/{id}` - Actualizar usuario
- `GET /roles` - Listar roles del tenant
- `POST /roles` - Crear rol personalizado
- `PUT /roles/{id}/permissions` - Asignar permisos a rol

### Bitácora (`/api/v1/audit`)
- `GET /logs` - Búsqueda de audit logs (con filtros)
- `GET /logs/export` - Exportar CSV de logs

## 📦 Celery - Tareas Asíncronas

### Worker (Celery)
Procesa tareas en background:
- `recalculate_obligations_matrix` - Recalcular matriz tras cambio en empresa
- `generate_compliance_report_pdf` - Generar reporte PDF
- `import_companies_csv` - Importación masiva
- `send_notification_email` - Envío de emails

### Beat (Scheduler)
Tareas periódicas:
- `check_expiring_obligations` - Alertas de vencimientos (diario)
- `cleanup_old_audit_logs` - Limpieza de logs antiguos (semanal)

**Configuración:**
- Broker: `redis://redis:6379/0`
- Backend: `redis://redis:6379/1`
- Retry policy + DLQ (Dead Letter Queue) en roadmap

## 🐳 Docker Compose - Servicios

```yaml
services:
  - postgres       # Base de datos principal
  - redis          # Broker Celery + cache
  - minio          # Storage S3-compatible
  - api            # FastAPI backend
  - celery-worker  # Worker asíncrono
  - celery-beat    # Scheduler
  - frontend       # Svelte dev server (prod usa build estático)
  - nginx          # Reverse proxy
```

## 🧪 Comandos para Probar

### 1. Levantar servicios
```bash
docker-compose up -d
```

### 2. Verificar que todo está up
```bash
docker-compose ps
```

### 3. Ejecutar migraciones
```bash
docker-compose exec api alembic upgrade head
```

### 4. Ejecutar seed (datos iniciales)
```bash
docker-compose exec api python scripts/seed.py
```

### 5. Login como superadmin (obtener token)
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@codebridge.com",
    "password": "SuperAdmin123!"
  }'
```

Respuesta:
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "superadmin@codebridge.com",
    "full_name": "Super Admin",
    "is_superadmin": true
  }
}
```

### 6. Crear nuevo tenant (con token de superadmin)
```bash
curl -X POST http://localhost:8000/api/v1/admin/tenants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -d '{
    "name": "Mi Empresa Test",
    "subdomain": "mi-empresa",
    "admin_email": "admin@miempresa.com",
    "admin_password": "Admin123!",
    "admin_full_name": "Admin Mi Empresa",
    "license": {
      "max_users": 10,
      "max_storage_gb": 50,
      "enabled_modules": ["companies", "obligations", "projects", "evidences"],
      "expires_at": "2026-12-31T23:59:59"
    }
  }'
```

### 7. Login como admin del tenant
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: mi-empresa" \
  -d '{
    "email": "admin@miempresa.com",
    "password": "Admin123!"
  }'
```

### 8. Crear empresa (con token de tenant admin)
```bash
curl -X POST http://localhost:8000/api/v1/companies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "X-Tenant-ID: mi-empresa" \
  -d '{
    "name": "Empresa Industrial S.A.",
    "rfc": "EIN123456789",
    "region": "NORTE",
    "installed_capacity_kw": 5000,
    "voltage_level": "MEDIA",
    "has_generation": false
  }'
```

### 9. Obtener presigned URL para subir evidencia
```bash
curl -X POST http://localhost:8000/api/v1/evidences/upload-url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "X-Tenant-ID: mi-empresa" \
  -d '{
    "filename": "reporte-consumo-2024.pdf",
    "content_type": "application/pdf",
    "company_id": 1
  }'
```

Respuesta:
```json
{
  "upload_url": "http://localhost:9000/bucket/path?X-Amz-Signature=...",
  "file_key": "tenant-mi-empresa/evidences/uuid.pdf",
  "expires_in": 300
}
```

### 10. Upload archivo a MinIO (presigned URL)
```bash
curl -X PUT "{PRESIGNED_URL}" \
  -H "Content-Type: application/pdf" \
  --upload-file reporte-consumo-2024.pdf
```

### 11. Registrar evidencia en DB
```bash
curl -X POST http://localhost:8000/api/v1/evidences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "X-Tenant-ID: mi-empresa" \
  -d '{
    "file_key": "tenant-mi-empresa/evidences/uuid.pdf",
    "filename": "reporte-consumo-2024.pdf",
    "content_type": "application/pdf",
    "size_bytes": 1048576,
    "company_id": 1,
    "description": "Reporte de consumo anual 2024"
  }'
```

### 12. Ver bitácora (audit logs)
```bash
curl -X GET "http://localhost:8000/api/v1/audit/logs?limit=20" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "X-Tenant-ID: mi-empresa"
```

### 13. Acceder al frontend
Abre tu navegador en: http://localhost:5173

Login con:
- **Email:** `admin@miempresa.com`
- **Password:** `Admin123!`

Verás el dashboard y sidebar con módulos según permisos.

## 🔒 Seguridad

### Passwords
- Hashing con **Argon2** (resistente a GPU cracking)
- Política mínima: 8 caracteres, 1 mayúscula, 1 número, 1 especial
- Política por tenant (opcional): rotación, histórico

### JWT Tokens
- **Access token:** 15 min (configurable)
- **Refresh token:** 7 días, rotación en cada refresh
- Algoritmo: RS256 (asymmetric keys en roadmap)
- Invalidación de refresh tokens en logout

### Rate Limiting
- Por IP: 100 req/min (general)
- Login endpoint: 5 intentos/min
- Middleware `slowapi` (implementación básica)

### CORS
- Whitelist de origins configurables por entorno
- Credentials habilitados para cookies (si usas)

### Secrets Management
- Variables de entorno (`.env`)
- No hardcodear secretos en código
- Roadmap: integración con Vault/AWS Secrets Manager

## 📈 Roadmap MVP (4-6 Sprints)

### Sprint 1-2: Fundación (HECHO)
- ✅ Arquitectura multi-tenant + RBAC + auditoría
- ✅ Auth JWT con refresh
- ✅ CRUD core: Tenants, Users, Roles, Companies
- ✅ Storage MinIO con presigned URLs
- ✅ Docker Compose completo
- ✅ Frontend: Login, Dashboard, Sidebar con permisos

### Sprint 3: Módulos Core I
- Perfilado automático (motor de reglas básico)
- Matriz de obligaciones (visualización + edición)
- Proyectos + tareas (CRUD completo)
- Celery: recalcular matriz, recordatorios

### Sprint 4: Módulos Core II
- Evidencias: versionado, tags, búsqueda por metadata
- Cotizaciones: workflow (borrador → enviada → aceptada/rechazada)
- Generación de PDFs (reportes básicos)
- Notificaciones in-app

### Sprint 5: UX + Features Enterprise
- Command Palette (CTRL+K)
- Keyboard shortcuts avanzados (navegación por tabla con flechas)
- Import/Export CSV (empresas, obligaciones)
- Filtros avanzados y búsqueda full-text
- Mobile: menú hamburguesa, gestos

### Sprint 6: Hardening + Producción
- Tests E2E (Playwright)
- Tests de carga (Locust)
- Monitoring: Prometheus + Grafana
- Logging estructurado (JSON + ELK)
- CI/CD (GitHub Actions)
- Deployment: Kubernetes manifests + Helm chart
- Backups automáticos (Postgres + MinIO)

## ⚠️ Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| Fuga de datos cross-tenant | 🔴 Crítico | Tests automáticos de aislamiento, code reviews obligatorios, scoping en ORM |
| Saturación de storage (MinIO) | 🟡 Medio | Quotas por tenant, alertas al 80%, cleanup de archivos huérfanos |
| Celery tasks fallidas sin retry | 🟡 Medio | Retry policy + exponential backoff, DLQ para errores persistentes |
| Escalabilidad horizontal limitada | 🟡 Medio | Diseño stateless, sessions en Redis, preparar para K8s |
| Dependencia de subdominio para tenancy | 🟢 Bajo | Fallback a header X-Tenant-ID, soporte multi-estrategia |
| Complejidad de motor de reglas | 🟡 Medio | MVP con reglas simples (if-then), roadmap motor DSL o integración con Drools |

## 🧑‍💻 Desarrollo Local (sin Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Celery Worker
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

### Celery Beat
```bash
cd backend
celery -A app.workers.celery_app beat --loglevel=info
```

## 📚 Documentación Adicional

- **API Docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Arquitectura detallada:** Ver sección "ARQUITECTURA" más abajo
- **Modelo de datos:** Ver sección "MODELO DE DATOS" más abajo

## 📞 Soporte

**Desarrollado por:** CodeBridge - Jorge Ernesto Herrera Cazares  
**Licencia:** Propietario  
**Versión:** 1.0.0-MVP

---

# ARQUITECTURA DETALLADA

## Diagrama de Componentes (Textual)

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET/USERS                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   NGINX (443)   │  ← Reverse Proxy + TLS
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
      ┌───────▼────────┐          ┌────────▼────────┐
      │  FRONTEND (80) │          │   API (8000)    │
      │   Svelte 5     │          │    FastAPI      │
      │   (Static)     │          │   (Async)       │
      └────────────────┘          └────────┬────────┘
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                  ┌───────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
                  │  PostgreSQL  │  │   Redis   │  │    MinIO    │
                  │   (Tenant    │  │  (Broker  │  │ (S3 Storage)│
                  │    Data)     │  │  + Cache) │  │             │
                  └──────────────┘  └─────┬─────┘  └─────────────┘
                                          │
                                  ┌───────▼────────┐
                                  │ Celery Worker  │
                                  │  + Beat        │
                                  │ (Async Tasks)  │
                                  └────────────────┘
```

## Flujos Clave

### 1. Autenticación y Multi-Tenancy
```
Usuario → Login (email + password + X-Tenant-ID)
  ↓
FastAPI → Validar credenciales (Argon2)
  ↓
FastAPI → Verificar tenant activo y licencia vigente
  ↓
FastAPI → Generar access token (15min) + refresh token (7 días)
  ↓
Cliente → Almacena tokens en memoria/localStorage
  ↓
Siguientes requests → Header: Authorization: Bearer {access_token}
  ↓
Middleware TenantContext → Extrae tenant_id y valida
  ↓
Middleware RBAC → Verifica permisos del usuario
  ↓
Endpoint → Ejecuta con scope de tenant_id automático
```

### 2. Upload de Evidencia (Presigned URL)
```
Usuario → Click "Subir Evidencia"
  ↓
Frontend → POST /evidences/upload-url {filename, content_type}
  ↓
API → Genera presigned PUT URL en MinIO (válida 5 min)
  ↓
API → Retorna {upload_url, file_key}
  ↓
Frontend → PUT {upload_url} con archivo binario (directo a MinIO)
  ↓
MinIO → Almacena archivo
  ↓
Frontend → POST /evidences {file_key, metadata} (tras upload exitoso)
  ↓
API → Guarda registro en DB con tenant_id
  ↓
Auditoría → Registra evento "evidence.create"
```

### 3. Recálculo de Matriz (Async)
```
Usuario → Actualiza datos de empresa (capacidad instalada)
  ↓
API → PUT /companies/{id} → Actualiza DB
  ↓
API → celery_app.send_task("recalculate_obligations_matrix", args=[company_id])
  ↓
Celery Worker → Ejecuta motor de reglas
  ↓
Worker → Lee obligaciones aplicables según perfil
  ↓
Worker → Actualiza company_obligations (estados)
  ↓
Worker → Marca task como SUCCESS
  ↓
(Opcional) → Notifica usuario vía WebSocket o polling
```

---

# MODELO DE DATOS COMPLETO

## ERD (Entidad-Relación Textual)

### Tablas Globales (sin tenant_id)
```
tenants
  - id: int PK
  - name: str (único)
  - subdomain: str (único, para multi-tenancy por subdominio)
  - status: enum (active, suspended, grace_period)
  - created_at: timestamp
  - updated_at: timestamp

licenses
  - id: int PK
  - tenant_id: int FK → tenants.id (1:1)
  - max_users: int
  - max_storage_gb: int
  - enabled_modules: jsonb (lista de module keys)
  - expires_at: timestamp
  - created_at: timestamp
  - updated_at: timestamp

modules (catálogo global)
  - id: int PK
  - key: str (único, ej: "companies", "obligations")
  - name: str
  - description: str
  - icon: str (nombre de icono)
  - shortcut_key: str (ej: "E" para empresas)
  - sort_order: int
  - is_active: bool
```

### Autenticación y RBAC (tenant-scoped)
```
users
  - id: int PK
  - tenant_id: int FK → tenants.id (null si superadmin)
  - email: str (único por tenant)
  - hashed_password: str (Argon2)
  - full_name: str
  - is_active: bool
  - is_superadmin: bool (solo para admin global)
  - last_login_at: timestamp
  - created_at: timestamp
  - updated_at: timestamp
  - INDEX (tenant_id, email)

roles
  - id: int PK
  - tenant_id: int FK → tenants.id (null para roles globales)
  - name: str (ej: "Admin", "Operador", "Auditor")
  - description: str
  - is_system: bool (no editable por tenant)
  - created_at: timestamp
  - updated_at: timestamp
  - UNIQUE (tenant_id, name)

permissions
  - id: int PK
  - module_id: int FK → modules.id
  - action: str (read, create, update, delete, approve, export, import, manage_users, view_audit, manage_billing)
  - description: str
  - UNIQUE (module_id, action)

role_permissions (many-to-many)
  - id: int PK
  - role_id: int FK → roles.id
  - permission_id: int FK → permissions.id
  - UNIQUE (role_id, permission_id)

user_roles (many-to-many)
  - id: int PK
  - user_id: int FK → users.id
  - role_id: int FK → roles.id
  - UNIQUE (user_id, role_id)

refresh_tokens
  - id: int PK
  - user_id: int FK → users.id
  - token_hash: str (hashed refresh token)
  - expires_at: timestamp
  - revoked_at: timestamp (null si activo)
  - created_at: timestamp
  - INDEX (user_id, revoked_at)
```

### Auditoría
```
audit_logs
  - id: int PK
  - tenant_id: int FK → tenants.id (null para eventos globales)
  - user_id: int FK → users.id (null para eventos del sistema)
  - module_key: str
  - action: str
  - entity_type: str (ej: "company", "project", "user")
  - entity_id: int
  - before_data: jsonb (resumen antes del cambio)
  - after_data: jsonb (resumen después del cambio)
  - ip_address: str
  - user_agent: str
  - request_id: str (UUID para tracing)
  - created_at: timestamp
  - INDEX (tenant_id, created_at DESC)
  - INDEX (user_id, created_at DESC)
  - INDEX (module_key, action)
```

### Módulos Core
```
companies (expediente empresarial)
  - id: int PK
  - tenant_id: int FK → tenants.id
  - name: str
  - rfc: str (RFC en México)
  - region: str (ej: NORTE, SUR, CENTRO)
  - installed_capacity_kw: float
  - voltage_level: str (BAJA, MEDIA, ALTA)
  - has_generation: bool
  - address: str
  - contact_name: str
  - contact_email: str
  - contact_phone: str
  - status: str (active, inactive)
  - created_at: timestamp
  - updated_at: timestamp
  - INDEX (tenant_id, status)

obligations (catálogo normativo global)
  - id: int PK
  - code: str (único, ej: "CDR-01-01")
  - title: str
  - description: text
  - category: str (ej: "SEGURIDAD", "OPERACION", "AMBIENTAL")
  - sub_category: str
  - normative_reference: str
  - frequency: str (única, anual, semestral, mensual)
  - applies_to: jsonb (criterios: voltage_level, has_generation, capacity_range)
  - is_active: bool
  - created_at: timestamp
  - updated_at: timestamp

company_obligations (matriz de cumplimiento)
  - id: int PK
  - tenant_id: int FK → tenants.id
  - company_id: int FK → companies.id
  - obligation_id: int FK → obligations.id
  - status: str (compliant, in_progress, non_compliant, not_applicable, pending_review)
  - notes: text
  - responsible_user_id: int FK → users.id
  - due_date: date
  - last_reviewed_at: timestamp
  - created_at: timestamp
  - updated_at: timestamp
  - UNIQUE (tenant_id, company_id, obligation_id)
  - INDEX (tenant_id, company_id, status)

projects (planes de trabajo)
  - id: int PK
  - tenant_id: int FK → tenants.id
  - company_id: int FK → companies.id
  - obligation_id: int FK → obligations.id (opcional, proyecto puede no estar ligado)
  - name: str
  - description: text
  - status: str (planning, in_progress, completed, cancelled, on_hold)
  - priority: str (low, medium, high, critical)
  - start_date: date
  - end_date: date
  - progress_percent: int (0-100)
  - budget: decimal
  - created_at: timestamp
  - updated_at: timestamp
  - INDEX (tenant_id, company_id, status)

tasks (tareas dentro de proyectos)
  - id: int PK
  - tenant_id: int FK → tenants.id
  - project_id: int FK → projects.id
  - title: str
  - description: text
  - assigned_user_id: int FK → users.id
  - status: str (pending, in_progress, completed, blocked)
  - due_date: date
  - completed_at: timestamp
  - created_at: timestamp
  - updated_at: timestamp
  - INDEX (tenant_id, project_id, status)

evidences (expediente electrónico)
  - id: int PK
  - tenant_id: int FK → tenants.id
  - company_id: int FK → companies.id (opcional)
  - project_id: int FK → projects.id (opcional)
  - obligation_id: int FK → obligations.id (opcional)
  - file_key: str (path en MinIO)
  - filename: str
  - content_type: str
  - size_bytes: bigint
  - description: text
  - tags: jsonb (array de strings)
  - checksum: str (SHA256)
  - version: int (para versionado futuro)
  - uploaded_by_user_id: int FK → users.id
  - uploaded_at: timestamp
  - expires_at: timestamp (opcional, para docs temporales)
  - created_at: timestamp
  - updated_at: timestamp
  - INDEX (tenant_id, company_id)
  - INDEX (file_key) (búsqueda rápida)

quotes (cotizaciones/propuestas)
  - id: int PK
  - tenant_id: int FK → tenants.id
  - company_id: int FK → companies.id
  - quote_number: str (auto-generado, ej: COT-2024-001)
  - title: str
  - description: text
  - status: str (draft, sent, accepted, rejected, expired)
  - subtotal: decimal
  - tax_percent: decimal
  - tax_amount: decimal
  - total: decimal
  - currency: str (ej: MXN, USD)
  - valid_until: date
  - sent_at: timestamp
  - accepted_at: timestamp
  - created_by_user_id: int FK → users.id
  - created_at: timestamp
  - updated_at: timestamp
  - INDEX (tenant_id, company_id, status)

quote_items (items/servicios dentro de cotización)
  - id: int PK
  - tenant_id: int FK → tenants.id
  - quote_id: int FK → quotes.id
  - description: str
  - quantity: decimal
  - unit_price: decimal
  - subtotal: decimal
  - sort_order: int
  - created_at: timestamp
  - updated_at: timestamp
```

### Constraints y Triggers (Conceptual)
```sql
-- Prevenir eliminación de tenant con datos
ALTER TABLE tenants ADD CONSTRAINT prevent_delete_with_users
  CHECK (status != 'deleted' OR NOT EXISTS (SELECT 1 FROM users WHERE users.tenant_id = tenants.id));

-- Auto-update updated_at
CREATE TRIGGER update_updated_at_timestamp
  BEFORE UPDATE ON companies
  FOR EACH ROW
  EXECUTE FUNCTION trigger_set_timestamp();

-- Validar límite de usuarios por licencia (lógica en backend)
-- Validar storage quota (lógica en backend + cron)
```

---

# CONTRATOS API (DTOs Pydantic v2)

## Auth Schemas

```python
# Login Request
{
  "email": "admin@tenant-demo.com",
  "password": "Admin123!"
}

# Login Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": 2,
    "email": "admin@tenant-demo.com",
    "full_name": "Admin Demo",
    "tenant_id": 1,
    "is_superadmin": false,
    "roles": ["Admin"],
    "permissions": {
      "companies": ["read", "create", "update", "delete", "export"],
      "obligations": ["read", "update"],
      "projects": ["read", "create", "update", "delete"],
      ...
    }
  }
}

# Refresh Request
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}

# Refresh Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",  # nuevo access token
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",  # nuevo refresh token (rotación)
  "token_type": "bearer",
  "expires_in": 900
}
```

## Tenant Admin Schemas

```python
# Create Tenant Request
{
  "name": "Mi Empresa Industrial S.A.",
  "subdomain": "mi-empresa",
  "admin_email": "admin@miempresa.com",
  "admin_password": "Admin123!",
  "admin_full_name": "Juan Pérez Administrador",
  "license": {
    "max_users": 20,
    "max_storage_gb": 100,
    "enabled_modules": ["companies", "obligations", "projects", "evidences", "quotes", "users", "audit"],
    "expires_at": "2026-12-31T23:59:59Z"
  }
}

# Create Tenant Response
{
  "id": 3,
  "name": "Mi Empresa Industrial S.A.",
  "subdomain": "mi-empresa",
  "status": "active",
  "license": {
    "id": 3,
    "max_users": 20,
    "max_storage_gb": 100,
    "current_users": 1,
    "current_storage_gb": 0.0,
    "enabled_modules": ["companies", "obligations", "projects", "evidences", "quotes", "users", "audit"],
    "expires_at": "2026-12-31T23:59:59Z"
  },
  "admin_user": {
    "id": 10,
    "email": "admin@miempresa.com",
    "full_name": "Juan Pérez Administrador"
  },
  "created_at": "2024-02-22T10:30:00Z"
}
```

## Company Schemas

```python
# Create Company Request
{
  "name": "Aceros del Norte S.A. de C.V.",
  "rfc": "ADN850215ABC",
  "region": "NORTE",
  "installed_capacity_kw": 8500.0,
  "voltage_level": "MEDIA",
  "has_generation": false,
  "address": "Carretera Nacional Km 25, Apodaca, N.L.",
  "contact_name": "Ing. Roberto Martínez",
  "contact_email": "rmartinez@acerosdelnorte.com",
  "contact_phone": "+52 81 8888 9999"
}

# Create Company Response
{
  "id": 5,
  "tenant_id": 3,
  "name": "Aceros del Norte S.A. de C.V.",
  "rfc": "ADN850215ABC",
  "region": "NORTE",
  "installed_capacity_kw": 8500.0,
  "voltage_level": "MEDIA",
  "has_generation": false,
  "address": "Carretera Nacional Km 25, Apodaca, N.L.",
  "contact_name": "Ing. Roberto Martínez",
  "contact_email": "rmartinez@acerosdelnorte.com",
  "contact_phone": "+52 81 8888 9999",
  "status": "active",
  "created_at": "2024-02-22T11:00:00Z",
  "updated_at": "2024-02-22T11:00:00Z"
}

# Get Company Matrix Response
{
  "company": {
    "id": 5,
    "name": "Aceros del Norte S.A. de C.V.",
    "rfc": "ADN850215ABC"
  },
  "obligations": [
    {
      "id": 1,
      "code": "CDR-01-01",
      "title": "Registro ante CRE",
      "category": "SEGURIDAD",
      "status": "compliant",
      "notes": "Registro actualizado en 2024",
      "responsible_user": {
        "id": 10,
        "full_name": "Juan Pérez"
      },
      "due_date": "2024-12-31",
      "last_reviewed_at": "2024-02-15T09:00:00Z"
    },
    {
      "id": 2,
      "code": "CDR-02-05",
      "title": "Mantenimiento preventivo anual",
      "category": "OPERACION",
      "status": "in_progress",
      "notes": "Programado para marzo 2024",
      "responsible_user": {
        "id": 11,
        "full_name": "María González"
      },
      "due_date": "2024-03-31",
      "last_reviewed_at": null
    },
    ...
  ],
  "summary": {
    "total": 45,
    "compliant": 30,
    "in_progress": 10,
    "non_compliant": 3,
    "not_applicable": 2,
    "compliance_percentage": 66.7
  }
}
```

## Project Schemas

```python
# Create Project Request
{
  "company_id": 5,
  "obligation_id": 2,  # opcional
  "name": "Implementación de Mantenimiento Preventivo 2024",
  "description": "Plan anual de mantenimiento según obligación CDR-02-05",
  "priority": "high",
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "budget": 150000.00
}

# Create Project Response
{
  "id": 8,
  "tenant_id": 3,
  "company_id": 5,
  "obligation_id": 2,
  "name": "Implementación de Mantenimiento Preventivo 2024",
  "description": "Plan anual de mantenimiento según obligación CDR-02-05",
  "status": "planning",
  "priority": "high",
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "progress_percent": 0,
  "budget": 150000.00,
  "created_at": "2024-02-22T11:30:00Z",
  "updated_at": "2024-02-22T11:30:00Z",
  "tasks_count": 0
}

# Create Task Request
{
  "project_id": 8,
  "title": "Inspección de transformadores",
  "description": "Revisar y documentar estado de 5 transformadores principales",
  "assigned_user_id": 11,
  "due_date": "2024-03-10"
}
```

## Evidence Schemas

```python
# Generate Presigned Upload URL Request
{
  "filename": "reporte-inspeccion-transformadores.pdf",
  "content_type": "application/pdf",
  "company_id": 5,
  "project_id": 8,  # opcional
  "description": "Reporte de inspección marzo 2024"
}

# Generate Presigned Upload URL Response
{
  "upload_url": "http://localhost:9000/evidences/tenant-mi-empresa/c9e7f3a4-uuid.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Signature=...",
  "file_key": "tenant-mi-empresa/evidences/c9e7f3a4-uuid.pdf",
  "expires_in": 300  # 5 minutos
}

# Register Evidence Request (tras upload exitoso a MinIO)
{
  "file_key": "tenant-mi-empresa/evidences/c9e7f3a4-uuid.pdf",
  "filename": "reporte-inspeccion-transformadores.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2048576,
  "company_id": 5,
  "project_id": 8,
  "obligation_id": 2,
  "description": "Reporte de inspección marzo 2024",
  "tags": ["inspeccion", "transformadores", "2024-Q1"],
  "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}

# Register Evidence Response
{
  "id": 15,
  "tenant_id": 3,
  "company_id": 5,
  "project_id": 8,
  "obligation_id": 2,
  "file_key": "tenant-mi-empresa/evidencias/c9e7f3a4-uuid.pdf",
  "filename": "reporte-inspeccion-transformadores.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2048576,
  "description": "Reporte de inspección marzo 2024",
  "tags": ["inspeccion", "transformadores", "2024-Q1"],
  "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "version": 1,
  "uploaded_by": {
    "id": 11,
    "full_name": "María González"
  },
  "uploaded_at": "2024-02-22T12:00:00Z",
  "created_at": "2024-02-22T12:00:05Z"
}

# Get Download URL Response
{
  "download_url": "http://localhost:9000/evidences/tenant-mi-empresa/c9e7f3a4-uuid.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&...",
  "expires_in": 300,
  "filename": "reporte-inspeccion-transformadores.pdf"
}
```

## Audit Schemas

```python
# List Audit Logs Request (Query Params)
GET /api/v1/audit/logs?user_id=11&module_key=companies&action=create&start_date=2024-02-01&end_date=2024-02-29&limit=50&offset=0

# List Audit Logs Response
{
  "items": [
    {
      "id": 125,
      "tenant_id": 3,
      "user": {
        "id": 11,
        "full_name": "María González",
        "email": "mgonzalez@miempresa.com"
      },
      "module_key": "companies",
      "action": "create",
      "entity_type": "company",
      "entity_id": 5,
      "after_data": {
        "name": "Aceros del Norte S.A. de C.V.",
        "rfc": "ADN850215ABC"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "request_id": "a7b3c4d5-uuid",
      "created_at": "2024-02-22T11:00:00Z"
    },
    {
      "id": 126,
      "tenant_id": 3,
      "user": {
        "id": 11,
        "full_name": "María González",
        "email": "mgonzalez@miempresa.com"
      },
      "module_key": "projects",
      "action": "update",
      "entity_type": "project",
      "entity_id": 8,
      "before_data": {
        "status": "planning",
        "progress_percent": 0
      },
      "after_data": {
        "status": "in_progress",
        "progress_percent": 25
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "request_id": "b8c4d5e6-uuid",
      "created_at": "2024-02-22T14:30:00Z"
    }
  ],
  "total": 127,
  "limit": 50,
  "offset": 0
}
```

---

Ahora generaré todos los archivos del repositorio:

<function_calls>
<invoke name="manage_todo_list">
<parameter name="operation">write