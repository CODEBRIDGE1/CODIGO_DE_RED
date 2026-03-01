"""
Admin Router - Security Levels (Niveles de Seguridad)
CRUD de niveles de seguridad con módulos accesibles por tenant.
Solo accesible para superadmin.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional, List
from datetime import datetime

from app.api.dependencies import get_current_superadmin, get_db
from app.models.user import User
from app.models.security_level import SecurityLevel, security_level_modules
from app.models.module import Module
from pydantic import BaseModel, Field

router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────────────────

class ModuleResponse(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0

    class Config:
        from_attributes = True


class SecurityLevelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: str = Field("blue", max_length=20)
    module_ids: List[int] = Field(default_factory=list)


class SecurityLevelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    module_ids: Optional[List[int]] = None


class SecurityLevelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    color: str
    is_active: bool
    created_at: datetime
    modules: List[ModuleResponse] = []
    users_count: int = 0

    class Config:
        from_attributes = True


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/modules/", response_model=List[ModuleResponse])
async def list_modules(
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Listar todos los módulos del sistema disponibles."""
    result = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.sort_order)
    )
    return result.scalars().all()


@router.get("/", response_model=List[SecurityLevelResponse])
async def list_security_levels(
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Listar todos los niveles de seguridad con sus módulos."""
    result = await db.execute(
        select(SecurityLevel).order_by(SecurityLevel.name)
    )
    levels = result.scalars().all()

    # Contar usuarios por nivel
    from sqlalchemy import func
    count_result = await db.execute(
        select(User.security_level_id, func.count(User.id).label("cnt"))
        .where(User.security_level_id.isnot(None))
        .group_by(User.security_level_id)
    )
    counts = {row.security_level_id: row.cnt for row in count_result}

    response = []
    for level in levels:
        data = SecurityLevelResponse.model_validate(level)
        data.users_count = counts.get(level.id, 0)
        response.append(data)

    return response


@router.get("/{level_id}", response_model=SecurityLevelResponse)
async def get_security_level(
    level_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener un nivel de seguridad por ID."""
    result = await db.execute(
        select(SecurityLevel).where(SecurityLevel.id == level_id)
    )
    level = result.scalar_one_or_none()
    if not level:
        raise HTTPException(status_code=404, detail="Nivel de seguridad no encontrado")

    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(User.id)).where(User.security_level_id == level_id)
    )
    users_count = count_result.scalar() or 0

    data = SecurityLevelResponse.model_validate(level)
    data.users_count = users_count
    return data


@router.post("/", response_model=SecurityLevelResponse, status_code=201)
async def create_security_level(
    payload: SecurityLevelCreate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Crear nuevo nivel de seguridad con módulos asignados."""
    # Verificar nombre único
    existing = await db.execute(
        select(SecurityLevel).where(SecurityLevel.name == payload.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un nivel con ese nombre")

    # Verificar que los módulos existan
    modules = []
    if payload.module_ids:
        result = await db.execute(
            select(Module).where(Module.id.in_(payload.module_ids))
        )
        modules = result.scalars().all()
        if len(modules) != len(payload.module_ids):
            raise HTTPException(status_code=400, detail="Uno o más módulos no existen")

    level = SecurityLevel(
        name=payload.name,
        description=payload.description,
        color=payload.color,
        is_active=True,
        modules=modules,
    )
    db.add(level)
    await db.commit()
    await db.refresh(level)

    data = SecurityLevelResponse.model_validate(level)
    data.users_count = 0
    return data


@router.put("/{level_id}", response_model=SecurityLevelResponse)
async def update_security_level(
    level_id: int,
    payload: SecurityLevelUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar nivel de seguridad (nombre, descripción, color, módulos)."""
    result = await db.execute(
        select(SecurityLevel).where(SecurityLevel.id == level_id)
    )
    level = result.scalar_one_or_none()
    if not level:
        raise HTTPException(status_code=404, detail="Nivel de seguridad no encontrado")

    update_data = payload.model_dump(exclude_unset=True)

    # Si se actualizan módulos, reemplazar la lista
    if "module_ids" in update_data:
        module_ids = update_data.pop("module_ids")
        if module_ids is not None:
            result = await db.execute(
                select(Module).where(Module.id.in_(module_ids))
            )
            modules = result.scalars().all()
            if len(modules) != len(module_ids):
                raise HTTPException(status_code=400, detail="Uno o más módulos no existen")
            level.modules = modules

    # Verificar nombre único si se cambia
    if "name" in update_data and update_data["name"] != level.name:
        existing = await db.execute(
            select(SecurityLevel).where(
                SecurityLevel.name == update_data["name"],
                SecurityLevel.id != level_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe un nivel con ese nombre")

    for field, value in update_data.items():
        setattr(level, field, value)

    level.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(level)

    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(User.id)).where(User.security_level_id == level_id)
    )
    users_count = count_result.scalar() or 0

    data = SecurityLevelResponse.model_validate(level)
    data.users_count = users_count
    return data


@router.delete("/{level_id}")
async def delete_security_level(
    level_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar nivel de seguridad (solo si no tiene usuarios asignados)."""
    result = await db.execute(
        select(SecurityLevel).where(SecurityLevel.id == level_id)
    )
    level = result.scalar_one_or_none()
    if not level:
        raise HTTPException(status_code=404, detail="Nivel de seguridad no encontrado")

    # Verificar que no tenga usuarios
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(User.id)).where(User.security_level_id == level_id)
    )
    users_count = count_result.scalar() or 0
    if users_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar: {users_count} usuario(s) tienen este nivel asignado"
        )

    await db.delete(level)
    await db.commit()
    return {"message": "Nivel de seguridad eliminado correctamente"}
