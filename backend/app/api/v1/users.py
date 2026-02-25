"""
Users Router
Endpoints para gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.api.dependencies import get_current_active_user

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Listar usuarios con paginación y filtros
    Filtra automáticamente por tenant_id del usuario autenticado
    """
    # Query base
    query = select(User)
    
    # Filtros
    filters = []
    
    # FILTRO POR TENANT: Solo ver usuarios de su organización
    if not current_user.is_superadmin:
        filters.append(User.tenant_id == current_user.tenant_id)
    
    if search:
        filters.append(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    if is_active is not None:
        filters.append(User.is_active == is_active)
    
    if filters:
        query = query.where(*filters)
    
    # Contar total
    count_query = select(func.count()).select_from(User)
    if filters:
        count_query = count_query.where(*filters)
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Paginación
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        total=total,
        users=users,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener detalles de un usuario
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que pertenece al mismo tenant
    if not current_user.is_superadmin and user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para ver este usuario"
        )
    
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear nuevo usuario en la organización del usuario autenticado
    """
    # Verificar si el email ya existe
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Asignar automáticamente el tenant_id del usuario actual (si no es superadmin)
    tenant_id = user_data.tenant_id if current_user.is_superadmin else current_user.tenant_id
    
    if tenant_id:
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organización no encontrada"
            )
    
    # Crear usuario
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        is_active=user_data.is_active,
        tenant_id=tenant_id,
        is_superadmin=False  # Los usuarios normales no pueden crear superadmins
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar usuario
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que pertenece al mismo tenant
    if not current_user.is_superadmin and user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para editar este usuario"
        )
    
    # Actualizar campos
    if user_data.email is not None:
        # Verificar que el nuevo email no esté en uso
        result = await db.execute(
            select(User).where(User.email == user_data.email, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        user.email = user_data.email
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.password is not None:
        user.hashed_password = hash_password(user_data.password)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Eliminar usuario (soft delete - marcar como inactivo)
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que pertenece al mismo tenant
    if not current_user.is_superadmin and user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para eliminar este usuario"
        )
    
    # Soft delete
    user.is_active = False
    await db.commit()
    
    return None
