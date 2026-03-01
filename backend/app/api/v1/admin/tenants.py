"""
Admin Router - Tenants Management
CRUD de clientes/tenants (solo superadmin)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional
from datetime import datetime

from app.api.dependencies import get_current_superadmin, get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.license import License
from pydantic import BaseModel, Field, EmailStr

router = APIRouter()


# Schemas
class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    subdomain: str = Field(..., min_length=1, max_length=100)
    contact_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    subdomain: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class TenantResponse(BaseModel):
    id: int
    name: str
    subdomain: str
    status: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Estadísticas
    users_count: int = 0
    companies_count: int = 0
    projects_count: int = 0
    
    class Config:
        from_attributes = True


@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Crear nuevo tenant/cliente (solo superadmin)"""
    
    # Verificar que el subdomain no exista
    result = await db.execute(
        select(Tenant).where(Tenant.subdomain == tenant_data.subdomain)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subdomain already exists")
    
    # Crear tenant
    db_tenant = Tenant(**tenant_data.model_dump())
    db.add(db_tenant)
    
    await db.commit()
    await db.refresh(db_tenant)
    
    response = TenantResponse.model_validate(db_tenant)
    return response


@router.get("/")
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Listar tenants con filtros (solo superadmin)"""
    
    # Base query
    query = select(Tenant)
    count_query = select(func.count(Tenant.id))
    
    # Filtros
    filters = []
    if search:
        search_filter = or_(
            Tenant.name.ilike(f"%{search}%"),
            Tenant.subdomain.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if status is not None:
        filters.append(Tenant.status == status)
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Contar total
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginación
    query = query.order_by(Tenant.name).offset((page - 1) * page_size).limit(page_size)
    
    # Ejecutar
    result = await db.execute(query)
    tenants = result.scalars().all()
    
    # Obtener estadísticas por tenant
    from app.models.company import Company
    from app.models.project import Project
    
    tenants_with_stats = []
    for tenant in tenants:
        # Contar usuarios
        users_result = await db.execute(
            select(func.count(User.id)).where(User.tenant_id == tenant.id)
        )
        users_count = users_result.scalar()
        
        # Contar empresas
        companies_result = await db.execute(
            select(func.count(Company.id)).where(Company.tenant_id == tenant.id)
        )
        companies_count = companies_result.scalar()
        
        # Contar proyectos
        projects_result = await db.execute(
            select(func.count(Project.id)).where(Project.tenant_id == tenant.id)
        )
        projects_count = projects_result.scalar()
        
        tenant_dict = TenantResponse.model_validate(tenant).model_dump()
        tenant_dict['users_count'] = users_count
        tenant_dict['companies_count'] = companies_count
        tenant_dict['projects_count'] = projects_count
        tenants_with_stats.append(tenant_dict)
    
    return {
        "items": tenants_with_stats,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener detalle de un tenant (solo superadmin)"""
    
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Obtener estadísticas
    from app.models.company import Company
    from app.models.project import Project
    
    users_result = await db.execute(
        select(func.count(User.id)).where(User.tenant_id == tenant.id)
    )
    companies_result = await db.execute(
        select(func.count(Company.id)).where(Company.tenant_id == tenant.id)
    )
    projects_result = await db.execute(
        select(func.count(Project.id)).where(Project.tenant_id == tenant.id)
    )
    
    response = TenantResponse.model_validate(tenant)
    response.users_count = users_result.scalar()
    response.companies_count = companies_result.scalar()
    response.projects_count = projects_result.scalar()
    
    return response


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar tenant (solo superadmin)"""
    
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Actualizar campos
    update_data = tenant_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    
    await db.commit()
    await db.refresh(tenant)
    
    return TenantResponse.model_validate(tenant)


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Desactivar tenant (soft delete, solo superadmin)"""
    
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Soft delete
    from app.models.tenant import TenantStatus
    tenant.status = TenantStatus.INACTIVE
    
    await db.commit()
    
    return {"message": "Tenant deactivated successfully"}
