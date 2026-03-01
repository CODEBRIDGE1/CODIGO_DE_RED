"""
Authentication Router
Endpoints para login, refresh token, logout
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.schemas.auth import LoginRequest, TokenResponse, UserProfile, RefreshTokenRequest
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.config import settings
from app.db.session import get_db
from app.db.base import import_models
from app.api.dependencies import get_current_user

# Import all models to resolve relationships
import_models()

from app.models.user import User
from app.models.tenant import Tenant
from app.models.security_level import SecurityLevel

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint
    Autentica usuario y devuelve tokens JWT
    """
    # Buscar usuario por email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    # Verificar password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    # Si no es superadmin, verificar que el tenant esté activo
    if not user.is_superadmin and user.tenant_id:
        result = await db.execute(
            select(Tenant).where(Tenant.id == user.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if not tenant or (hasattr(tenant.status, 'value') and tenant.status.value != 'active'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant inactivo"
            )
    
    # Actualizar último login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Crear tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": user.tenant_id,
        "is_superadmin": user.is_superadmin
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh token endpoint
    Genera nuevo access token usando un refresh token válido
    """
    from app.core.security import decode_token

    payload = decode_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": user.tenant_id,
        "is_superadmin": user.is_superadmin
    }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user profile
    Devuelve información del usuario autenticado
    """
    from app.models.role import Role
    from app.models.permission import Permission
    from app.models.module import Module
    
    # Obtener nombre del tenant si existe
    tenant_name = None
    if current_user.tenant_id:
        result = await db.execute(
            select(Tenant).where(Tenant.id == current_user.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant:
            tenant_name = tenant.name
    
    # Obtener roles del usuario
    roles = []
    permissions_dict = {}
    
    if current_user.tenant_id:
        # Obtener roles del usuario con sus permisos
        result = await db.execute(
            select(Role)
            .join(Role.users)
            .where(User.id == current_user.id)
        )
        user_roles = result.scalars().all()
        roles = [role.name for role in user_roles]
        
        # Obtener todos los permisos de esos roles
        for role in user_roles:
            result = await db.execute(
                select(Permission)
                .join(Permission.roles)
                .join(Permission.module)
                .where(Role.id == role.id)
            )
            role_permissions = result.scalars().all()
            
            for perm in role_permissions:
                module_key = perm.module.key if perm.module else 'unknown'
                if module_key not in permissions_dict:
                    permissions_dict[module_key] = []
                if perm.action not in permissions_dict[module_key]:
                    permissions_dict[module_key].append(perm.action)
    
    # Obtener módulos del nivel de seguridad del usuario
    security_modules: list[str] = []
    security_level_id: int | None = current_user.security_level_id
    security_level_name: str | None = None
    if current_user.security_level_id:
        sl_result = await db.execute(
            select(SecurityLevel).where(SecurityLevel.id == current_user.security_level_id)
        )
        security_level = sl_result.scalar_one_or_none()
        if security_level:
            security_level_name = security_level.name
            security_modules = [m.key for m in security_level.modules]

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superadmin=current_user.is_superadmin,
        tenant_id=current_user.tenant_id,
        tenant_name=tenant_name,
        roles=roles,
        permissions=permissions_dict,
        security_modules=security_modules,
        security_level_id=security_level_id,
        security_level_name=security_level_name
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint
    Invalida tokens (requiere implementar blacklist de tokens)
    """
    # TODO: Implementar blacklist de tokens en Redis
    return {"message": "Logout exitoso"}
