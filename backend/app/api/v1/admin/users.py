"""
Admin Router - Users Management
CRUD de usuarios tenant (solo superadmin)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional
from datetime import datetime

from app.api.dependencies import get_current_superadmin, get_db
from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
from app.models.security_level import SecurityLevel
from app.core.security import hash_password
from pydantic import BaseModel, Field, EmailStr

router = APIRouter()


# Schemas
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=8)
    tenant_id: int
    is_active: bool = True
    security_level_id: Optional[int] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    password: Optional[str] = Field(None, min_length=8)
    tenant_id: Optional[int] = None
    is_active: Optional[bool] = None
    security_level_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_superadmin: bool
    tenant_id: Optional[int]
    tenant_name: Optional[str] = None
    security_level_id: Optional[int] = None
    security_level_name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None  # alias para last_login_at
    
    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Crear nuevo usuario tenant (solo superadmin)"""
    
    # Verificar que el email no exista
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verificar que el tenant exista
    result = await db.execute(
        select(Tenant).where(Tenant.id == user_data.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Tenant is not active")
    
    # Crear usuario
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        tenant_id=user_data.tenant_id,
        is_active=user_data.is_active,
        is_superadmin=False,
        security_level_id=user_data.security_level_id,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Obtener nombre del nivel de seguridad
    security_level_name = None
    if db_user.security_level_id:
        sl_result = await db.execute(
            select(SecurityLevel.name).where(SecurityLevel.id == db_user.security_level_id)
        )
        security_level_name = sl_result.scalar_one_or_none()

    # Agregar nombre del tenant
    response_data = UserResponse.model_validate(db_user)
    response_data.tenant_name = tenant.name
    response_data.security_level_name = security_level_name

    return response_data


@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    tenant_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Listar usuarios tenant con filtros (solo superadmin)"""
    
    # Base query con join al tenant y nivel de seguridad
    query = select(
        User,
        Tenant.name.label('tenant_name'),
        SecurityLevel.name.label('security_level_name')
    ).outerjoin(
        Tenant, User.tenant_id == Tenant.id
    ).outerjoin(
        SecurityLevel, User.security_level_id == SecurityLevel.id
    )
    count_query = select(func.count(User.id))
    
    # Filtros
    filters = [User.is_superadmin == False]  # No mostrar superadmins
    
    if search:
        search_filter = or_(
            User.email.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%"),
            Tenant.name.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if tenant_id is not None:
        filters.append(User.tenant_id == tenant_id)
    
    if is_active is not None:
        filters.append(User.is_active == is_active)
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Contar total
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginación
    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    
    # Ejecutar
    result = await db.execute(query)
    rows = result.all()
    
    # Construir respuesta con tenant_name y security_level_name
    users_list = []
    for user, tenant_name, security_level_name in rows:
        user_dict = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'is_active': user.is_active,
            'is_superadmin': user.is_superadmin,
            'tenant_id': user.tenant_id,
            'tenant_name': tenant_name,
            'security_level_id': user.security_level_id,
            'security_level_name': security_level_name,
            'created_at': user.created_at,
            'last_login': getattr(user, 'last_login_at', None)
        }
        users_list.append(user_dict)

    return users_list


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener usuario por ID (solo superadmin)"""
    
    result = await db.execute(
        select(User, Tenant.name.label('tenant_name')).outerjoin(
            Tenant, User.tenant_id == Tenant.id
        ).where(User.id == user_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    user, tenant_name = row
    
    response_data = UserResponse.model_validate(user)
    response_data.tenant_name = tenant_name
    
    return response_data


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar usuario (solo superadmin)"""
    
    # Buscar usuario
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.is_superadmin:
        raise HTTPException(status_code=400, detail="Cannot modify superadmin users")
    
    # Actualizar campos
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Si se actualiza el tenant, verificar que exista
    if 'tenant_id' in update_data and update_data['tenant_id'] is not None:
        result = await db.execute(
            select(Tenant).where(Tenant.id == update_data['tenant_id'])
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        if tenant.status != TenantStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Tenant is not active")
    
    # Si se actualiza la contraseña, hashearla
    if 'password' in update_data and update_data['password']:
        update_data['hashed_password'] = hash_password(update_data['password'])
        del update_data['password']
    
    # Aplicar actualizaciones
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    
    # Obtener nombre del tenant
    tenant_name = None
    if db_user.tenant_id:
        result = await db.execute(
            select(Tenant.name).where(Tenant.id == db_user.tenant_id)
        )
        tenant_name = result.scalar_one_or_none()

    # Obtener nombre del nivel de seguridad
    security_level_name = None
    if db_user.security_level_id:
        sl_result = await db.execute(
            select(SecurityLevel.name).where(SecurityLevel.id == db_user.security_level_id)
        )
        security_level_name = sl_result.scalar_one_or_none()

    response_data = UserResponse.model_validate(db_user)
    response_data.tenant_name = tenant_name
    response_data.security_level_name = security_level_name

    return response_data


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Desactivar usuario (solo superadmin)"""
    
    # Buscar usuario
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.is_superadmin:
        raise HTTPException(status_code=400, detail="Cannot delete superadmin users")
    
    # Desactivar en lugar de eliminar
    db_user.is_active = False
    
    await db.commit()
    
    return {"message": "User deactivated successfully"}
