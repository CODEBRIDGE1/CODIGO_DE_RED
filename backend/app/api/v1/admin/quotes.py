"""
Admin Router - Cotizaciones
Lista y gestiona todas las cotizaciones de todos los tenants (solo superadmin)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal

from app.api.dependencies import get_current_superadmin, get_db
from app.models.user import User
from app.models.quote import Quote, QuoteLine
from app.models.company import Company
from app.models.tenant import Tenant

router = APIRouter()


class AdminQuoteLineOut(BaseModel):
    id: int
    quote_item_id: Optional[int]
    description: str
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class AdminQuoteOut(BaseModel):
    id: int
    quote_number: str
    title: str
    status: str
    total: Decimal
    iva_percent: Optional[int] = 16
    iva_amount: Optional[Decimal] = Decimal("0")
    total_con_iva: Optional[Decimal] = Decimal("0")
    fecha_vigencia: Optional[date] = None
    comentarios_admin: Optional[str] = None
    numero_transformadores: Optional[int]
    observaciones: Optional[str]
    created_at: datetime
    updated_at: datetime
    # Empresa
    company_id: int
    razon_social: str
    rfc: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado_empresa: Optional[str] = None
    codigo_postal: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    # Cliente (tenant)
    tenant_id: int
    cliente_nombre: str
    lines: list[AdminQuoteLineOut] = []

    model_config = {"from_attributes": True}


class AdminQuoteListOut(BaseModel):
    quotes: list[AdminQuoteOut]
    total: int
    page: int
    page_size: int


class AdminLinePriceUpdate(BaseModel):
    unit_price: Decimal


class AdminQuoteDetailsUpdate(BaseModel):
    iva_percent: Optional[int] = None          # 0, 8, 16
    fecha_vigencia: Optional[date] = None
    comentarios_admin: Optional[str] = None


class AdminQuoteStatusUpdate(BaseModel):
    status: str  # "approved" | "rejected" | "sent" | "draft"
    observaciones_admin: Optional[str] = None


def _build_quote_out(q: Quote) -> AdminQuoteOut:
    """Helper: construir AdminQuoteOut desde un objeto Quote con relaciones cargadas"""
    c = q.company
    return AdminQuoteOut(
        id=q.id,
        quote_number=q.quote_number,
        title=q.title,
        status=q.status,
        total=q.total,
        iva_percent=q.iva_percent if q.iva_percent is not None else 16,
        iva_amount=q.iva_amount or Decimal("0"),
        total_con_iva=q.total_con_iva or Decimal("0"),
        fecha_vigencia=q.fecha_vigencia,
        comentarios_admin=q.comentarios_admin,
        numero_transformadores=q.numero_transformadores,
        observaciones=q.observaciones,
        created_at=q.created_at,
        updated_at=q.updated_at,
        company_id=q.company_id,
        razon_social=c.razon_social if c else "—",
        rfc=c.rfc if c else None,
        direccion=c.direccion if c else None,
        ciudad=c.ciudad if c else None,
        estado_empresa=c.estado if c else None,
        codigo_postal=c.codigo_postal if c else None,
        telefono=c.telefono if c else None,
        email=c.email if c else None,
        tenant_id=q.tenant_id,
        cliente_nombre=q.tenant.name if q.tenant else "—",
        lines=[AdminQuoteLineOut.model_validate(l) for l in q.lines],
    )


_QUOTE_OPTIONS = [
    selectinload(Quote.lines),
    selectinload(Quote.company),
    selectinload(Quote.tenant),
]


@router.get("/", response_model=AdminQuoteListOut)
async def list_all_quotes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query("sent", description="Filtrar por estado"),
    search: Optional[str] = None,
    tenant_id: Optional[int] = None,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Listar todas las cotizaciones de todos los tenants (solo superadmin)"""

    query = select(Quote).options(*_QUOTE_OPTIONS)
    count_query = select(func.count(Quote.id))

    filters = []
    if status and status != "all":
        filters.append(Quote.status == status)
    if tenant_id:
        filters.append(Quote.tenant_id == tenant_id)
    if search:
        filters.append(or_(
            Quote.quote_number.ilike(f"%{search}%"),
            Quote.title.ilike(f"%{search}%"),
        ))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Quote.created_at.desc()).limit(page_size).offset(offset)

    result = await db.execute(query)
    quotes = result.scalars().all()

    return AdminQuoteListOut(
        quotes=[_build_quote_out(q) for q in quotes],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{quote_id}", response_model=AdminQuoteOut)
async def get_quote(
    quote_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener cotización por ID (solo superadmin)"""
    result = await db.execute(
        select(Quote).options(*_QUOTE_OPTIONS).where(Quote.id == quote_id)
    )
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return _build_quote_out(quote)


@router.put("/{quote_id}/status", response_model=AdminQuoteOut)
async def update_quote_status(
    quote_id: int,
    payload: AdminQuoteStatusUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Cambiar estado de una cotización — solo superadmin"""
    allowed = {"sent", "approved", "rejected", "draft"}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Valores permitidos: {allowed}")

    result = await db.execute(
        select(Quote).options(*_QUOTE_OPTIONS).where(Quote.id == quote_id)
    )
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote.status = payload.status
    if payload.observaciones_admin:
        existing = quote.observaciones or ""
        quote.observaciones = f"{existing}\n[Admin] {payload.observaciones_admin}".strip()

    await db.commit()

    result2 = await db.execute(
        select(Quote).options(*_QUOTE_OPTIONS).where(Quote.id == quote_id)
    )
    return _build_quote_out(result2.scalar_one())


@router.put("/{quote_id}/lines/{line_id}/price", response_model=AdminQuoteLineOut)
async def update_line_price(
    quote_id: int,
    line_id: int,
    payload: AdminLinePriceUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar precio de una línea de cotización — solo superadmin"""
    result = await db.execute(
        select(QuoteLine).where(
            and_(QuoteLine.id == line_id, QuoteLine.quote_id == quote_id)
        )
    )
    line = result.scalar_one_or_none()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    line.unit_price = payload.unit_price
    line.subtotal = line.quantity * payload.unit_price
    await db.commit()

    # Recalcular total de la cotización
    total_result = await db.execute(
        select(func.sum(QuoteLine.subtotal)).where(QuoteLine.quote_id == quote_id)
    )
    new_total = total_result.scalar() or Decimal("0")
    quote_result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = quote_result.scalar_one()
    # Recalcular IVA y total con IVA
    iva_pct = quote.iva_percent or 0
    iva_amount = new_total * Decimal(str(iva_pct)) / Decimal("100")
    quote.total = new_total
    quote.iva_amount = iva_amount
    quote.total_con_iva = new_total + iva_amount
    await db.commit()

    await db.refresh(line)
    return line


@router.patch("/{quote_id}/details", response_model=AdminQuoteOut)
async def update_quote_details(
    quote_id: int,
    payload: AdminQuoteDetailsUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar IVA, fecha de vigencia y comentarios de una cotización — solo superadmin"""
    result = await db.execute(
        select(Quote).options(*_QUOTE_OPTIONS).where(Quote.id == quote_id)
    )
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if payload.iva_percent is not None:
        if payload.iva_percent not in (0, 8, 16):
            raise HTTPException(status_code=400, detail="IVA debe ser 0, 8 o 16")
        quote.iva_percent = payload.iva_percent
        # Recalcular IVA
        iva_amount = quote.total * Decimal(str(payload.iva_percent)) / Decimal("100")
        quote.iva_amount = iva_amount
        quote.total_con_iva = quote.total + iva_amount

    if payload.fecha_vigencia is not None:
        quote.fecha_vigencia = payload.fecha_vigencia

    if payload.comentarios_admin is not None:
        quote.comentarios_admin = payload.comentarios_admin

    await db.commit()

    result2 = await db.execute(
        select(Quote).options(*_QUOTE_OPTIONS).where(Quote.id == quote_id)
    )
    return _build_quote_out(result2.scalar_one())
