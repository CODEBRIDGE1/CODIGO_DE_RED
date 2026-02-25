"""
RBAC (Role-Based Access Control) Core
Dependencies y utilities para enforcement de permisos
"""
from typing import List, Set
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.tenant import get_current_tenant_id


class PermissionChecker:
    """
    Dependency para verificar permisos de usuario
    """
    
    def __init__(self, module_key: str, action: str):
        """
        Args:
            module_key: Clave del módulo (ej: "companies", "obligations")
            action: Acción requerida (ej: "read", "create", "update", "delete")
        """
        self.module_key = module_key
        self.action = action
    
    async def __call__(
        self,
        current_user: "User" = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> "User":
        """
        Verificar que usuario tenga el permiso requerido
        
        Returns:
            Usuario si tiene permiso
            
        Raises:
            HTTPException 403 si no tiene permiso
        """
        # Superadmins tienen acceso a todo
        if current_user.is_superadmin:
            return current_user
        
        # Verificar permiso específico
        has_permission = await check_user_permission(
            user=current_user,
            module_key=self.module_key,
            action=self.action,
            db=db
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tiene permiso para {self.action} en módulo {self.module_key}"
            )
        
        return current_user


async def check_user_permission(
    user: "User",
    module_key: str,
    action: str,
    db: AsyncSession
) -> bool:
    """
    Verificar si usuario tiene permiso específico
    
    Args:
        user: Usuario a verificar
        module_key: Clave del módulo
        action: Acción requerida
        db: Database session
        
    Returns:
        True si tiene permiso
    """
    from app.models.user import User
    from app.models.role import Role
    from app.models.permission import Permission
    from app.models.module import Module
    
    # Superadmins siempre tienen permiso
    if user.is_superadmin:
        return True
    
    # Query permisos del usuario a través de sus roles
    result = await db.execute(
        select(Permission)
        .join(Permission.roles)
        .join(Role.users)
        .join(Permission.module)
        .where(
            User.id == user.id,
            Module.key == module_key,
            Permission.action == action
        )
    )
    
    permission = result.scalar_one_or_none()
    return permission is not None


async def get_user_permissions(
    user: "User",
    db: AsyncSession
) -> dict[str, List[str]]:
    """
    Obtener todos los permisos del usuario organizados por módulo
    
    Args:
        user: Usuario
        db: Database session
        
    Returns:
        Dict {module_key: [action1, action2, ...]}
    """
    from app.models.user import User
    from app.models.role import Role
    from app.models.permission import Permission
    from app.models.module import Module
    
    # Superadmins tienen todos los permisos
    if user.is_superadmin:
        # Retornar todos los módulos y acciones posibles
        return await get_all_available_permissions(db)
    
    # Query permisos del usuario
    result = await db.execute(
        select(Module.key, Permission.action)
        .join(Permission.module)
        .join(Permission.roles)
        .join(Role.users)
        .where(User.id == user.id)
        .distinct()
    )
    
    rows = result.all()
    
    # Organizar por módulo
    permissions_dict: dict[str, List[str]] = {}
    for module_key, action in rows:
        if module_key not in permissions_dict:
            permissions_dict[module_key] = []
        permissions_dict[module_key].append(action)
    
    return permissions_dict


async def get_all_available_permissions(db: AsyncSession) -> dict[str, List[str]]:
    """
    Obtener todos los permisos disponibles en el sistema
    
    Args:
        db: Database session
        
    Returns:
        Dict {module_key: [action1, action2, ...]}
    """
    from app.models.permission import Permission
    from app.models.module import Module
    
    result = await db.execute(
        select(Module.key, Permission.action)
        .join(Permission.module)
        .where(Module.is_active == True)
    )
    
    rows = result.all()
    
    permissions_dict: dict[str, List[str]] = {}
    for module_key, action in rows:
        if module_key not in permissions_dict:
            permissions_dict[module_key] = []
        permissions_dict[module_key].append(action)
    
    return permissions_dict


async def check_module_enabled_for_tenant(
    module_key: str,
    tenant_id: int,
    db: AsyncSession
) -> bool:
    """
    Verificar si módulo está habilitado en licencia del tenant
    
    Args:
        module_key: Clave del módulo
        tenant_id: Tenant ID
        db: Database session
        
    Returns:
        True si módulo está habilitado
    """
    from app.models.license import License
    
    result = await db.execute(
        select(License).where(License.tenant_id == tenant_id)
    )
    license = result.scalar_one_or_none()
    
    if not license:
        return False
    
    # enabled_modules es un JSON array
    return module_key in (license.enabled_modules or [])


def require_permission(module_key: str, action: str):
    """
    Factory para crear dependency de verificación de permisos
    
    Usage:
        @router.get("/companies")
        async def list_companies(
            user: User = Depends(require_permission("companies", "read"))
        ):
            ...
    
    Args:
        module_key: Clave del módulo
        action: Acción requerida
        
    Returns:
        PermissionChecker dependency
    """
    return PermissionChecker(module_key, action)


def require_any_permission(module_key: str, actions: List[str]):
    """
    Verificar que usuario tenga AL MENOS UNA de las acciones especificadas
    
    Args:
        module_key: Clave del módulo
        actions: Lista de acciones (OR logic)
        
    Returns:
        Dependency callable
    """
    async def checker(
        current_user: "User" = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> "User":
        if current_user.is_superadmin:
            return current_user
        
        for action in actions:
            has_perm = await check_user_permission(
                user=current_user,
                module_key=module_key,
                action=action,
                db=db
            )
            if has_perm:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tiene permiso para ninguna de las acciones: {', '.join(actions)}"
        )
    
    return checker


def require_superadmin():
    """
    Dependency para verificar que usuario sea superadmin
    
    Usage:
        @router.post("/admin/tenants")
        async def create_tenant(
            user: User = Depends(require_superadmin())
        ):
            ...
    """
    async def checker(current_user: "User" = Depends(get_current_user)) -> "User":
        if not current_user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo superadmins pueden acceder a este recurso"
            )
        return current_user
    
    return checker


# Import circular fix - se importa al final
from app.api.v1.dependencies import get_current_user
