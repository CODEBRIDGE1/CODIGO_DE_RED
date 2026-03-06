#!/usr/bin/env python3
"""
Seed database with initial data
Run: python scripts/seed.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db.session import AsyncSessionLocal
from app.db.base import import_models
from app.core.security import hash_password

# Import all models first to avoid circular imports
import_models()

from app.models.tenant import Tenant, TenantStatus
from app.models.license import License
from app.models.user import User
from app.models.role import Role, UserRole, RolePermission
from app.models.module import Module
from app.models.permission import Permission

async def seed_database():
    print("🌱 Seeding database...")
    
    async with AsyncSessionLocal() as db:
        # 1. Create Modules (idempotent)
        modules_data = [
            {"key": "dashboard", "name": "Dashboard", "icon": "home", "shortcut_key": "D", "sort_order": 1},
            {"key": "companies", "name": "Empresas", "icon": "building", "shortcut_key": "E", "sort_order": 2},
            {"key": "obligations", "name": "Obligaciones", "icon": "checklist", "shortcut_key": "O", "sort_order": 3},
            {"key": "projects", "name": "Proyectos", "icon": "folder", "shortcut_key": "P", "sort_order": 4},
            {"key": "evidences", "name": "Evidencias", "icon": "file", "shortcut_key": "V", "sort_order": 5},
            {"key": "quotes", "name": "Cotizaciones", "icon": "document", "shortcut_key": "C", "sort_order": 6},
            {"key": "users", "name": "Usuarios", "icon": "users", "shortcut_key": "U", "sort_order": 7},
            {"key": "audit", "name": "Bitácora", "icon": "clock", "shortcut_key": "B", "sort_order": 8},
        ]
        
        modules = []
        modules_created = 0
        for mod_data in modules_data:
            result = await db.execute(select(Module).where(Module.key == mod_data["key"]))
            existing_module = result.scalar_one_or_none()
            if not existing_module:
                module = Module(**mod_data, is_active=True)
                db.add(module)
                modules.append(module)
                modules_created += 1
            else:
                modules.append(existing_module)
        
        await db.flush()
        if modules_created > 0:
            print(f"✓ Created {modules_created} modules")
        else:
            print(f"✓ Modules already exist (skipped)")
        
        # Reload modules to get their IDs
        result = await db.execute(select(Module))
        modules = list(result.scalars().all())
        
        # 2. Create Permissions (idempotent)
        actions = ["read", "create", "update", "delete", "export"]
        permissions = []
        permissions_created = 0
        for module in modules:
            for action in actions:
                if module.key == "dashboard" and action not in ["read"]:
                    continue
                result = await db.execute(
                    select(Permission).where(
                        Permission.module_id == module.id,
                        Permission.action == action
                    )
                )
                existing_perm = result.scalar_one_or_none()
                if not existing_perm:
                    perm = Permission(module_id=module.id, action=action, description=f"{action} {module.name}")
                    db.add(perm)
                    permissions.append(perm)
                    permissions_created += 1
                else:
                    permissions.append(existing_perm)
        
        await db.flush()
        if permissions_created > 0:
            print(f"✓ Created {permissions_created} permissions")
        else:
            print(f"✓ Permissions already exist (skipped)")
        
        # Reload all permissions
        result = await db.execute(select(Permission))
        permissions = list(result.scalars().all())
        
        # 3. Create Superadmin User (idempotent)
        result = await db.execute(select(User).where(User.email == "superadmin@codebridge.com"))
        superadmin = result.scalar_one_or_none()
        if not superadmin:
            superadmin = User(
                email="superadmin@codebridge.com",
                hashed_password=hash_password("SuperAdmin123!"),
                full_name="Super Admin",
                is_superadmin=True,
                is_active=True
            )
            db.add(superadmin)
            await db.flush()
            print(f"✓ Created superadmin user: {superadmin.email}")
        else:
            print(f"✓ Superadmin user already exists (skipped)")
        
        # 4. Create Demo Tenant (idempotent)
        result = await db.execute(select(Tenant).where(Tenant.subdomain == "tenant-demo"))
        demo_tenant = result.scalar_one_or_none()
        if not demo_tenant:
            demo_tenant = Tenant(
                name="Tenant Demo",
                subdomain="tenant-demo",
                status=TenantStatus.ACTIVE
            )
            db.add(demo_tenant)
            await db.flush()
            
            demo_license = License(
                tenant_id=demo_tenant.id,
                max_users=50,
                max_storage_gb=100,
                enabled_modules=["companies", "obligations", "projects", "evidences", "quotes", "users", "audit"],
                expires_at=datetime.utcnow() + timedelta(days=365)
            )
            db.add(demo_license)
            print(f"✓ Created demo tenant: {demo_tenant.subdomain}")
        else:
            print(f"✓ Demo tenant already exists (skipped)")
        
        # 5. Create Admin Role for Tenant (idempotent)
        result = await db.execute(
            select(Role).where(
                Role.tenant_id == demo_tenant.id,
                Role.name == "Admin"
            )
        )
        admin_role = result.scalar_one_or_none()
        if not admin_role:
            admin_role = Role(
                tenant_id=demo_tenant.id,
                name="Admin",
                description="Administrador con todos los permisos",
                is_system=True
            )
            db.add(admin_role)
            await db.flush()
            
            # Assign all permissions to admin role
            for perm in permissions:
                role_perm = RolePermission(role_id=admin_role.id, permission_id=perm.id)
                db.add(role_perm)
            print(f"✓ Created admin role for tenant")
        else:
            print(f"✓ Admin role already exists (skipped)")
        
        # 6. Create Admin User for Tenant (idempotent)
        result = await db.execute(select(User).where(User.email == "admin@tenant-demo.com"))
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                tenant_id=demo_tenant.id,
                email="admin@tenant-demo.com",
                hashed_password=hash_password("Admin123!"),
                full_name="Admin Demo",
                is_active=True,
                is_superadmin=False
            )
            db.add(admin_user)
            await db.flush()
            
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.add(user_role)
            print(f"✓ Created admin user for tenant: {admin_user.email}")
        else:
            print(f"✓ Admin user already exists (skipped)")
        
        # Commit all
        await db.commit()
        
        print("\n" + "="*60)
        print("✓ Database seeded successfully!")
        print("="*60)
        print("\nUSERS CREATED:")
        print(f"  Superadmin: superadmin@codebridge.com / SuperAdmin123!")
        print(f"  Tenant Admin: admin@tenant-demo.com / Admin123!")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(seed_database())
