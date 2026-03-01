"""
Admin Router - Companies Management
CRUD de empresas por tenant (solo superadmin)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.api.dependencies import get_current_superadmin, get_db
from app.models.user import User
from app.models.company import Company
from app.models.tenant import Tenant
from app.models.document import Document
from app.core.minio_client import minio_client
from pydantic import BaseModel, Field, EmailStr

router = APIRouter()


class CompanyResponse(BaseModel):
    id: int
    razon_social: str
    nombre_comercial: Optional[str] = None
    rfc: str
    rpu: Optional[str] = None
    tipo_suministro: str
    tension_suministro: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    is_active: bool
    clasificacion: Optional[str] = None
    demanda_contratada_kw: Optional[float] = None
    demanda_maxima_kw: Optional[float] = None
    consumo_mensual_kwh: Optional[float] = None
    costo_mensual_aproximado: Optional[float] = None
    notas: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyCreate(BaseModel):
    tenant_id: int
    razon_social: str = Field(..., min_length=1, max_length=300)
    nombre_comercial: Optional[str] = None
    rfc: str = Field(..., min_length=12, max_length=13)
    rpu: Optional[str] = Field(None, max_length=50)
    tipo_suministro: str = Field(..., pattern="^(GDMTH|GDMTO|GDBT|DIST)$")
    tension_suministro: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    demanda_contratada_kw: Optional[float] = None
    demanda_maxima_kw: Optional[float] = None
    consumo_mensual_kwh: Optional[float] = None
    costo_mensual_aproximado: Optional[float] = None
    nombre_centro_carga: Optional[str] = None
    notas: Optional[str] = None
    is_active: bool = True


class CompanyUpdate(BaseModel):
    razon_social: Optional[str] = Field(None, min_length=1, max_length=300)
    nombre_comercial: Optional[str] = None
    rfc: Optional[str] = Field(None, min_length=12, max_length=13)
    rpu: Optional[str] = Field(None, max_length=50)
    tipo_suministro: Optional[str] = Field(None, pattern="^(GDMTH|GDMTO|GDBT|DIST)$")
    tension_suministro: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    demanda_contratada_kw: Optional[float] = None
    demanda_maxima_kw: Optional[float] = None
    consumo_mensual_kwh: Optional[float] = None
    costo_mensual_aproximado: Optional[float] = None
    notas: Optional[str] = None
    is_active: Optional[bool] = None


def _calcular_clasificacion(data: dict) -> Optional[str]:
    """Clasificación automática por demanda contratada"""
    demanda = data.get("demanda_contratada_kw")
    if not demanda:
        return None
    if demanda >= 1000:
        return "Grande"
    elif demanda >= 500:
        return "Mediana"
    elif demanda >= 100:
        return "Pequeña"
    return "Micro"


@router.get("/")
async def list_companies(
    tenant_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Listar empresas con filtro por tenant (solo superadmin)"""

    query = select(Company)
    count_query = select(func.count(Company.id))

    filters = []

    if tenant_id is not None:
        filters.append(Company.tenant_id == tenant_id)

    if search:
        from sqlalchemy import or_
        search_filter = or_(
            Company.razon_social.ilike(f"%{search}%"),
            Company.nombre_comercial.ilike(f"%{search}%"),
            Company.rfc.ilike(f"%{search}%"),
            Company.rpu.ilike(f"%{search}%"),
        )
        filters.append(search_filter)

    if filters:
        from sqlalchemy import and_
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Company.razon_social).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    companies = result.scalars().all()

    return {
        "items": [CompanyResponse.model_validate(c) for c in companies],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ── Schemas de documentos para admin ────────────────────────────────────────

class AdminDocumentResponse(BaseModel):
    id: int
    company_id: int
    tenant_id: int
    tipo_documento: str
    nombre_original: str
    nombre_archivo: str
    mime_type: Optional[str] = None
    tamano_bytes: Optional[int] = None
    descripcion: Optional[str] = None
    vigencia: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Endpoints de documentos (admin, sin restricción de tenant) ───────────────

@router.get("/{company_id}/documents/")
async def admin_list_company_documents(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superadmin),
):
    """Listar todos los documentos de una empresa (superadmin)"""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    result = await db.execute(
        select(Document)
        .where(Document.company_id == company_id, Document.is_active == True)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return {
        "items": [AdminDocumentResponse.model_validate(d) for d in documents],
        "total": len(documents),
    }


@router.get("/{company_id}/documents/{document_id}/download/")
async def admin_download_document(
    company_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superadmin),
):
    """Obtener URL de descarga de un documento (superadmin)"""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.company_id == company_id,
            Document.is_active == True,
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    try:
        url = minio_client.get_presigned_url(
            bucket_name="documentos",
            object_name=document.ruta_minio,
            expires=60 * 60,
        )
        return {
            "url": url,
            "nombre_original": document.nombre_original,
            "mime_type": document.mime_type,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar URL: {str(e)}")

@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Crear empresa para un tenant (solo superadmin)"""

    # Verificar que el tenant exista
    result = await db.execute(select(Tenant).where(Tenant.id == company_data.tenant_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # RFC único
    result = await db.execute(select(Company).where(Company.rfc == company_data.rfc.upper()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El RFC ya está registrado")

    # RPU único
    result = await db.execute(select(Company).where(Company.rpu == company_data.rpu))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El RPU ya está registrado")

    data = company_data.model_dump()
    data["rfc"] = data["rfc"].upper()
    data["clasificacion"] = _calcular_clasificacion(data)

    company = Company(**data)
    db.add(company)
    await db.commit()
    await db.refresh(company)

    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar empresa (solo superadmin)"""

    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    update_data = company_data.model_dump(exclude_unset=True)

    # RFC único si se cambia
    if "rfc" in update_data and update_data["rfc"]:
        update_data["rfc"] = update_data["rfc"].upper()
        result = await db.execute(
            select(Company).where(Company.rfc == update_data["rfc"], Company.id != company_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="El RFC ya está registrado en otra empresa")

    # RPU único si se cambia
    if "rpu" in update_data and update_data["rpu"]:
        result = await db.execute(
            select(Company).where(Company.rpu == update_data["rpu"], Company.id != company_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="El RPU ya está registrado en otra empresa")

    # Recalcular clasificación si cambió la demanda
    if "demanda_contratada_kw" in update_data:
        update_data["clasificacion"] = _calcular_clasificacion(
            {**company.__dict__, **update_data}
        )

    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)

    return company



class CompanyResponse(BaseModel):
    id: int
    razon_social: str
    nombre_comercial: Optional[str] = None
    rfc: str
    rpu: str
    tipo_suministro: str
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    is_active: bool
    clasificacion: Optional[str] = None
    demanda_contratada_kw: Optional[float] = None
    consumo_mensual_kwh: Optional[float] = None
    costo_mensual_aproximado: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/")
async def list_companies(
    tenant_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Listar empresas con filtro por tenant (solo superadmin)"""

    query = select(Company)
    count_query = select(func.count(Company.id))

    filters = []

    if tenant_id is not None:
        filters.append(Company.tenant_id == tenant_id)

    if search:
        from sqlalchemy import or_
        search_filter = or_(
            Company.razon_social.ilike(f"%{search}%"),
            Company.nombre_comercial.ilike(f"%{search}%"),
            Company.rfc.ilike(f"%{search}%"),
            Company.rpu.ilike(f"%{search}%"),
        )
        filters.append(search_filter)

    if filters:
        from sqlalchemy import and_
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Company.razon_social).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    companies = result.scalars().all()

    return {
        "items": [CompanyResponse.model_validate(c) for c in companies],
        "total": total,
        "page": page,
        "page_size": page_size
    }
