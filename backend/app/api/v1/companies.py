"""
Companies Router
Endpoints para gestión de empresas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.api.dependencies import get_current_active_user

router = APIRouter()


def calcular_clasificacion(company_data: dict) -> str:
    """
    Calcular clasificación automática basada en tipo de suministro y demanda
    """
    tipo = company_data.get('tipo_suministro')
    demanda = company_data.get('demanda_contratada_kw') or 0
    
    # Convertir a float si es necesario y manejar None
    try:
        demanda = float(demanda) if demanda is not None else 0.0
    except (ValueError, TypeError):
        demanda = 0.0
    
    if tipo == 'GDMTH':
        if demanda >= 1000:
            return 'GDMTH-ALTO'
        elif demanda >= 500:
            return 'GDMTH-MEDIO'
        else:
            return 'GDMTH-BAJO'
    elif tipo == 'GDMTO':
        if demanda >= 500:
            return 'GDMTO-ALTO'
        else:
            return 'GDMTO-MEDIO'
    elif tipo == 'GDBT':
        return 'GDBT'
    else:
        return tipo


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=1000),
    search: Optional[str] = None,
    tipo_suministro: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Listar empresas del tenant del usuario autenticado
    """
    query = select(Company)
    
    filters = []
    
    # FILTRO POR TENANT: Solo ver empresas de su organización
    if not current_user.is_superadmin:
        filters.append(Company.tenant_id == current_user.tenant_id)
    
    if search:
        filters.append(
            or_(
                Company.razon_social.ilike(f"%{search}%"),
                Company.nombre_comercial.ilike(f"%{search}%"),
                Company.rfc.ilike(f"%{search}%"),
                Company.rpu.ilike(f"%{search}%")
            )
        )
    
    if tipo_suministro:
        filters.append(Company.tipo_suministro == tipo_suministro)
    
    if is_active is not None:
        filters.append(Company.is_active == is_active)
    
    if filters:
        query = query.where(*filters)
    
    # Contar total
    count_query = select(func.count()).select_from(Company)
    if filters:
        count_query = count_query.where(*filters)
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Paginación
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Company.created_at.desc())
    
    result = await db.execute(query)
    companies = result.scalars().all()
    
    return CompanyListResponse(
        total=total,
        companies=companies,
        page=page,
        page_size=page_size
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener detalles de una empresa
    """
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    # Verificar que pertenece al mismo tenant
    if not current_user.is_superadmin and company.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para ver esta empresa"
        )
    
    return company


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear nueva empresa
    """
    # Verificar si el RFC ya existe
    result = await db.execute(
        select(Company).where(Company.rfc == company_data.rfc.upper())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El RFC ya está registrado"
        )
    
    # Verificar si el RPU ya existe (solo si se proporcionó)
    if company_data.rpu:
        result = await db.execute(
            select(Company).where(Company.rpu == company_data.rpu)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El RPU ya está registrado"
            )
    
    # Calcular clasificación automática
    clasificacion = calcular_clasificacion(company_data.model_dump())
    
    # Crear empresa
    company = Company(
        **company_data.model_dump(),
        tenant_id=current_user.tenant_id,
        clasificacion=clasificacion
    )
    
    db.add(company)
    await db.commit()
    await db.refresh(company)
    
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar empresa
    """
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    # Verificar que pertenece al mismo tenant
    if not current_user.is_superadmin and company.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para editar esta empresa"
        )
    
    # Actualizar campos
    update_data = company_data.model_dump(exclude_unset=True)
    
    # Verificar RFC único si se está cambiando
    if 'rpu' in update_data and update_data['rpu'] and update_data['rpu'] != company.rpu:
        result = await db.execute(
            select(Company).where(
                Company.rpu == update_data['rpu'],
                Company.id != company_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El RPU ya está registrado por otra empresa"
            )

    if 'rfc' in update_data and update_data['rfc'] != company.rfc:
        result = await db.execute(
            select(Company).where(
                Company.rfc == update_data['rfc'].upper(),
                Company.id != company_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El RFC ya está registrado"
            )
        update_data['rfc'] = update_data['rfc'].upper()
    
    # Actualizar
    for field, value in update_data.items():
        setattr(company, field, value)
    
    # Recalcular clasificación si cambió algo relevante
    if any(k in update_data for k in ['tipo_suministro', 'demanda_contratada_kw']):
        company.clasificacion = calcular_clasificacion({
            'tipo_suministro': company.tipo_suministro,
            'demanda_contratada_kw': company.demanda_contratada_kw
        })
    
    await db.commit()
    await db.refresh(company)
    
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Eliminar empresa (soft delete)
    """
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    # Verificar que pertenece al mismo tenant
    if not current_user.is_superadmin and company.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para eliminar esta empresa"
        )
    
    # Soft delete
    company.is_active = False
    await db.commit()
    
    return None
