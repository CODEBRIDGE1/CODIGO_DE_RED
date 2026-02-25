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
        # 1. Create Modules
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
        for mod_data in modules_data:
            module = Module(**mod_data, is_active=True)
            db.add(module)
            modules.append(module)
        await db.flush()
        print(f"✓ Created {len(modules)} modules")
        
        # 2. Create Permissions
        actions = ["read", "create", "update", "delete", "export"]
        permissions = []
        for module in modules:
            for action in actions:
                if module.key == "dashboard" and action not in ["read"]:
                    continue
                perm = Permission(module_id=module.id, action=action, description=f"{action} {module.name}")
                db.add(perm)
                permissions.append(perm)
        await db.flush()
        print(f"✓ Created {len(permissions)} permissions")
        
        # 3. Create Superadmin User
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
        
        # 4. Create Demo Tenant
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
        
        # 5. Create Admin Role for Tenant
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
        
        # 6. Create Admin User for Tenant
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
