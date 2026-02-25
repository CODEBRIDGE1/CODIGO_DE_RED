# 📋 GUÍA DE LA PLATAFORMA CÓDIGO DE RED

## 🎯 ¿Qué es este Dashboard?

Este dashboard es el **portal del cliente** (tenant). Cada empresa que contrata tu servicio tendrá acceso a este dashboard para gestionar su propia información.

---

## 👥 Tipos de Usuarios en el Sistema

### 1. **SUPERADMIN (TÚ - CodeBridge)**
- Email: `superadmin@codebridge.com`
- **No pertenece a ningún tenant** (tenant_id = null)
- Puede ver y gestionar TODOS los tenants/clientes
- Acceso total a configuración global
- **Dashboard diferente** (aún no implementado, será el panel de administración de CodeBridge)

### 2. **ADMIN DEL CLIENTE (Tenant Admin)**
- Email: `admin@tenant-demo.com` 
- **Pertenece a un tenant específico** (tenant_id = 1)
- Ve solo los usuarios de SU empresa
- Este es el dashboard que estás viendo ahora
- Puede gestionar usuarios, empresas, proyectos, etc. DE SU ORGANIZACIÓN

### 3. **USUARIOS REGULARES DEL CLIENTE**
- Son empleados de la empresa cliente
- Acceso limitado según sus roles/permisos
- Solo ven datos de su propia empresa

---

## 🏢 Estructura Multi-Tenant

```
CodeBridge (TÚ)
│
├── Tenant 1: "Empresa Demo S.A."
│   ├── admin@tenant-demo.com (administrador)
│   ├── usuario1@tenant-demo.com
│   ├── usuario2@tenant-demo.com
│   └── Sus propios datos: empresas, proyectos, evidencias
│
├── Tenant 2: "Industrias XYZ"
│   ├── admin@industriasxyz.com
│   └── Sus propios datos (completamente aislados del Tenant 1)
│
└── Tenant 3: "Manufactura ABC"
    └── ...
```

---

## 📊 Módulo de Usuarios y Roles - ¿Qué Ves?

Cuando entras a **"Usuarios y Roles"** con `admin@tenant-demo.com`, verás:

### ✅ Usuarios Actuales en la Base de Datos:

1. **superadmin@codebridge.com** 
   - Rol: SUPERADMIN
   - Tenant: Ninguno (es de CodeBridge)
   - **NOTA**: Este NO debería aparecer en el listado del cliente
   
2. **admin@tenant-demo.com**
   - Rol: Admin del Tenant "Demo"
   - Tenant: Empresa Demo (tenant_id = 1)
   - **Este SÍ aparece** porque pertenece al tenant

### 🔒 Filtrado por Tenant (Próxima Mejora)

**IMPORTANTE**: Actualmente el endpoint `/api/v1/users` lista TODOS los usuarios, pero debería:
- Filtrar automáticamente por el `tenant_id` del usuario logueado
- Solo mostrar usuarios de SU empresa
- Ocultar el superadmin y usuarios de otros tenants

---

## ⚙️ Funcionalidades del Módulo de Usuarios

### 1. **Ver Listado de Usuarios**
- Tabla con todos los usuarios de tu organización
- Información: Nombre, Email, Último acceso, Fecha de registro, Estado
- Avatares con iniciales

### 2. **Buscar y Filtrar**
- Búsqueda por nombre o email
- Filtro por estado (Activos/Inactivos)
- Paginación (10 usuarios por página)

### 3. **Crear Nuevo Usuario**
- Botón "Nuevo Usuario" (atajo: N)
- Formulario con:
  - Nombre completo
  - Email (único)
  - Contraseña (mínimo 8 caracteres)
  - Estado activo/inactivo

### 4. **Editar Usuario**
- Click en el ícono de editar (lápiz)
- Modificar nombre, email, contraseña
- Activar/desactivar usuario

### 5. **Activar/Desactivar Usuario**
- Click en el badge de estado (Verde = Activo, Rojo = Inactivo)
- Confirmación antes de cambiar
- "Soft delete" (no se elimina, solo se desactiva)

---

## 🔐 Roles y Permisos (Conceptual)

### Permisos Actuales (Hardcoded en Login)
```javascript
permissions: [
  'empresas.read', 'empresas.create', 'empresas.update',
  'obligaciones.read', 'obligaciones.update',
  'proyectos.read', 'proyectos.create', 'proyectos.update',
  'evidencias.read', 'evidencias.create',
  'cotizaciones.read', 'cotizaciones.create',
  'reportes.read',
  'usuarios.read',
  'auditoria.read'
]
```

### Próximas Implementaciones:
- **Tabla `roles`**: Admin, Usuario, Auditor, Visor
- **Tabla `permissions`**: Lista de todos los permisos granulares
- **Tabla `role_permissions`**: Qué permisos tiene cada rol
- **Tabla `user_roles`**: Qué roles tiene cada usuario
- **Sistema RBAC completo** en backend con decoradores

---

## 🎨 Navegación del Dashboard

### Atajos de Teclado (Keyboard-First)
- `ALT + D` → Dashboard
- `ALT + E` → Empresas
- `ALT + O` → Obligaciones
- `ALT + P` → Proyectos
- `ALT + V` → Evidencias
- `ALT + C` → Cotizaciones
- `ALT + R` → Reportes
- `ALT + U` → Usuarios
- `ALT + A` → Auditoría

### Sidebar
- Menú colapsable
- Indicador visual de página activa
- Permisos: Solo ve los módulos que tiene permitidos

---

## 🔄 Próximos Pasos Recomendados

### 1. **Implementar Filtro por Tenant en Backend**
```python
# En /api/v1/users.py
# Agregar middleware o dependency que obtenga el tenant_id del token JWT
# Filtrar automáticamente: query.where(User.tenant_id == current_user.tenant_id)
```

### 2. **Dashboard de SuperAdmin (Para TI)**
- Panel separado para `superadmin@codebridge.com`
- Gestión de todos los tenants
- Métricas globales
- Configuración de planes y licencias

### 3. **Sistema de Roles Completo**
- Crear tablas de roles y permisos
- CRUD de roles por tenant
- Asignación de roles a usuarios
- Enforcement en todos los endpoints

### 4. **Auditoría de Acciones**
- Registrar quién creó/editó/desactivó usuarios
- Tabla `audit_log` con todas las acciones
- Módulo de Auditoría funcional

### 5. **Validaciones de Negocio**
- Límite de usuarios por plan del tenant
- Verificar licencia activa antes de crear usuarios
- Notificaciones cuando se acerquen al límite

---

## 📝 Cómo Probar el Módulo de Usuarios

1. **Inicia sesión** en http://localhost:5173
   - Email: `admin@tenant-demo.com`
   - Password: `Admin123!`

2. **Navega a Usuarios**
   - Click en "Usuarios y Roles" en el sidebar
   - O presiona `ALT + U`

3. **Ver Listado**
   - Deberías ver los 2 usuarios actuales
   - (superadmin y admin@tenant-demo.com)

4. **Crear Usuario**
   - Click en "Nuevo Usuario"
   - Llena el formulario
   - Ejemplo:
     - Nombre: Juan Pérez
     - Email: juan.perez@tenant-demo.com
     - Password: Usuario123!
   - Click "Crear Usuario"

5. **Editar Usuario**
   - Click en el ícono de lápiz
   - Modifica el nombre
   - Click "Guardar Cambios"

6. **Desactivar Usuario**
   - Click en el badge verde "Activo"
   - Confirma la acción
   - El badge cambia a rojo "Inactivo"

---

## 🐛 Debugging

### Ver logs del backend:
```bash
docker-compose logs api --tail 50 -f
```

### Ver logs del frontend:
```bash
docker-compose logs frontend --tail 50 -f
```

### Ver usuarios en la base de datos:
```bash
docker-compose exec api python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text('SELECT id, email, full_name, tenant_id FROM users'))
        for row in result:
            print(f'{row[0]} | {row[1]} | {row[2]} | Tenant: {row[3]}')

asyncio.run(check())
"
```

---

## 💡 Resumen

**Dashboard Actual = Portal del Cliente**
- Cada empresa (tenant) ve solo sus datos
- Los usuarios de una empresa solo ven usuarios de su empresa
- Sistema multi-tenant con aislamiento de datos

**Próximo Dashboard = Panel de CodeBridge**
- Para ti (superadmin)
- Gestión de todos los clientes
- Configuración global
- Métricas de toda la plataforma

---

¿Necesitas que implemente el filtro por tenant en los endpoints o prefieres trabajar en otro módulo?
