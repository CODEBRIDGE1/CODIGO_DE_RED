"""
Quotes API - Cotizaciones para Tenants
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload
from typing import Optional
from decimal import Decimal

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.quote import Quote, QuoteLine
from app.models.company import Company
from app.models.compliance import CompanyClassification
from app.models.quote_item import QuoteItem
from app.schemas.quote import (
    QuoteCreate,
    QuoteUpdate,
    QuoteResponse,
    QuoteListResponse,
    QuoteLineResponse
)
from app.schemas.quote_item import QuoteItemResponse, QuoteItemListResponse

router = APIRouter()


def generate_quote_number(tenant_id: int, count: int) -> str:
    """Generar número de cotización: COT-{tenant_id}-{count+1:04d}"""
    return f"COT-{tenant_id}-{count+1:04d}"


@router.post("/", response_model=QuoteResponse, status_code=201)
async def create_quote(
    quote_data: QuoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crear nueva cotización"""
    
    # Verificar que la empresa pertenece al tenant
    result = await db.execute(
        select(Company).where(
            and_(
                Company.id == quote_data.company_id,
                Company.tenant_id == current_user.tenant_id
            )
        )
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Contar cotizaciones existentes para generar el número
    count_result = await db.execute(
        select(func.count(Quote.id)).where(Quote.tenant_id == current_user.tenant_id)
    )
    count = count_result.scalar() or 0
    
    # Crear cotización
    db_quote = Quote(
        tenant_id=current_user.tenant_id,
        company_id=quote_data.company_id,
        quote_number=generate_quote_number(current_user.tenant_id, count),
        title=quote_data.title,
        numero_transformadores=quote_data.numero_transformadores,
        observaciones=quote_data.observaciones,
        total=Decimal('0')
    )
    db.add(db_quote)
    await db.flush()
    
    # Agregar líneas
    total = Decimal('0')
    for line_data in quote_data.lines:
        subtotal = line_data.quantity * line_data.unit_price
        db_line = QuoteLine(
            tenant_id=current_user.tenant_id,
            quote_id=db_quote.id,
            quote_item_id=line_data.quote_item_id,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            subtotal=subtotal
        )
        db.add(db_line)
        total += subtotal
    
    # Actualizar total
    db_quote.total = total
    
    await db.commit()
    await db.refresh(db_quote)
    
    # Cargar relaciones
    result = await db.execute(
        select(Quote).where(Quote.id == db_quote.id)
    )
    quote = result.scalar_one()
    
    await db.refresh(quote, ['lines', 'company'])
    
    # Obtener tipo_centro_carga
    tipo_result = await db.execute(
        select(CompanyClassification).where(CompanyClassification.company_id == quote.company_id)
    )
    classification = tipo_result.scalar_one_or_none()
    
    response = QuoteResponse.model_validate(quote)
    response.tipo_centro_carga = classification.tipo_centro_carga.value if classification else None
    response.razon_social = company.razon_social
    
    return response


@router.get("/", response_model=QuoteListResponse)
async def list_quotes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    company_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Listar cotizaciones del tenant"""
    
    # Base query
    query = select(Quote).where(Quote.tenant_id == current_user.tenant_id)
    count_query = select(func.count(Quote.id)).where(Quote.tenant_id == current_user.tenant_id)
    
    # Filtros
    if search:
        search_filter = or_(
            Quote.quote_number.ilike(f"%{search}%"),
            Quote.title.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    if status:
        query = query.where(Quote.status == status)
        count_query = count_query.where(Quote.status == status)
    
    if company_id:
        query = query.where(Quote.company_id == company_id)
        count_query = count_query.where(Quote.company_id == company_id)
    
    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginación
    offset = (page - 1) * page_size
    query = query.order_by(Quote.created_at.desc()).limit(page_size).offset(offset)
    
    # Ejecutar query
    result = await db.execute(query)
    quotes = result.scalars().all()
    
    # Cargar relaciones y construir respuesta
    quotes_response = []
    for quote in quotes:
        await db.refresh(quote, ['lines', 'company'])
        
        # Obtener tipo_centro_carga
        tipo_result = await db.execute(
            select(CompanyClassification).where(CompanyClassification.company_id == quote.company_id)
        )
        classification = tipo_result.scalar_one_or_none()
        
        quote_resp = QuoteResponse.model_validate(quote)
        quote_resp.tipo_centro_carga = classification.tipo_centro_carga.value if classification else None
        quote_resp.razon_social = quote.company.razon_social
        quotes_response.append(quote_resp)
    
    return QuoteListResponse(
        quotes=quotes_response,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/catalog", response_model=QuoteItemListResponse)
async def list_catalog_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Listar conceptos del catálogo disponibles para cotizar (solo activos)"""
    
    # Base query - solo items activos
    query = select(QuoteItem).where(QuoteItem.is_active == True)
    count_query = select(func.count(QuoteItem.id)).where(QuoteItem.is_active == True)
    
    # Filtros
    if search:
        search_filter = or_(
            QuoteItem.code.ilike(f"%{search}%"),
            QuoteItem.name.ilike(f"%{search}%"),
            QuoteItem.description.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    if category:
        query = query.where(QuoteItem.category == category)
        count_query = count_query.where(QuoteItem.category == category)
    
    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginación
    offset = (page - 1) * page_size
    query = query.order_by(QuoteItem.code).limit(page_size).offset(offset)
    
    # Ejecutar query
    result = await db.execute(query)
    items = result.scalars().all()
    
    return QuoteItemListResponse(
        items=[QuoteItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener cotización por ID"""
    
    result = await db.execute(
        select(Quote)
        .options(selectinload(Quote.lines), selectinload(Quote.company))
        .where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Obtener tipo_centro_carga
    tipo_result = await db.execute(
        select(CompanyClassification).where(CompanyClassification.company_id == quote.company_id)
    )
    classification = tipo_result.scalar_one_or_none()
    
    response = QuoteResponse.model_validate(quote)
    response.tipo_centro_carga = classification.tipo_centro_carga.value if classification else None
    response.razon_social = quote.company.razon_social
    
    return response


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: int,
    quote_data: QuoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar cotización"""
    
    result = await db.execute(
        select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Solo se pueden modificar cotizaciones en borrador (excepto cambio de draft→sent)
    updating_only_status = (
        quote_data.title is None and
        quote_data.numero_transformadores is None and
        quote_data.observaciones is None and
        quote_data.lines is None and
        quote_data.status is not None
    )
    if quote.status != 'draft' and not updating_only_status:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden editar cotizaciones en borrador"
        )

    # Validar transiciones de estado permitidas para el tenant
    if quote_data.status is not None:
        valid_transitions: dict[str, str] = {
            'draft': 'sent',
            'approved': 'accepted',
        }
        expected = valid_transitions.get(quote.status)
        if expected != quote_data.status:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede cambiar el estado de '{quote.status}' a '{quote_data.status}'"
            )

    # Actualizar campos básicos
    if quote_data.title is not None:
        quote.title = quote_data.title
    if quote_data.numero_transformadores is not None:
        quote.numero_transformadores = quote_data.numero_transformadores
    if quote_data.observaciones is not None:
        quote.observaciones = quote_data.observaciones
    if quote_data.status is not None:
        quote.status = quote_data.status
    
    # Si se envían líneas, actualizar todo el detalle
    if quote_data.lines is not None:
        # Eliminar líneas existentes con DELETE SQL directo (evita lazy loading)
        await db.execute(
            delete(QuoteLine).where(QuoteLine.quote_id == quote_id)
        )
        
        # Crear nuevas líneas
        total = Decimal('0')
        for line_data in quote_data.lines:
            subtotal = line_data.quantity * line_data.unit_price
            new_line = QuoteLine(
                tenant_id=current_user.tenant_id,
                quote_id=quote.id,
                quote_item_id=line_data.quote_item_id,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                subtotal=subtotal
            )
            db.add(new_line)
            total += subtotal
        
        quote.total = total
    
    await db.commit()
    
    # Recargar con relaciones usando selectinload
    result2 = await db.execute(
        select(Quote)
        .options(selectinload(Quote.lines), selectinload(Quote.company))
        .where(Quote.id == quote_id)
    )
    quote = result2.scalar_one()
    
    # Obtener tipo_centro_carga
    tipo_result = await db.execute(
        select(CompanyClassification).where(CompanyClassification.company_id == quote.company_id)
    )
    classification = tipo_result.scalar_one_or_none()
    
    response = QuoteResponse.model_validate(quote)
    response.tipo_centro_carga = classification.tipo_centro_carga.value if classification else None
    response.razon_social = quote.company.razon_social
    
    return response


@router.delete("/{quote_id}", status_code=204)
async def delete_quote(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar cotización"""
    
    result = await db.execute(
        select(Quote).where(
            and_(
                Quote.id == quote_id,
                Quote.tenant_id == current_user.tenant_id
            )
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote.status != 'draft':
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden eliminar cotizaciones en borrador"
        )
    
    await db.delete(quote)
    await db.commit()
    
    return None

