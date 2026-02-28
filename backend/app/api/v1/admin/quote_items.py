"""
Admin Router - Quote Items Catalog
CRUD de conceptos/partidas para cotizaciones (solo superadmin)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional

from app.api.dependencies import get_current_superadmin, get_db
from app.models.user import User
from app.models.quote_item import QuoteItem, TenantQuoteItemPrice
from app.schemas.quote_item import (
    QuoteItemCreate,
    QuoteItemUpdate,
    QuoteItemResponse,
    QuoteItemListResponse
)

router = APIRouter()


@router.post("/quote-items", response_model=QuoteItemResponse, status_code=201)
async def create_quote_item(
    item_data: QuoteItemCreate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Crear nuevo concepto en el catálogo (solo superadmin)"""
    
    # Verificar que el código no exista
    result = await db.execute(
        select(QuoteItem).where(QuoteItem.code == item_data.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Code already exists")
    
    # Crear concepto
    db_item = QuoteItem(
        **item_data.model_dump(),
        created_by=current_user.id
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    
    return db_item


@router.get("/quote-items", response_model=QuoteItemListResponse)
async def list_quote_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Listar conceptos del catálogo con filtros (solo superadmin)"""
    
    # Base query
    query = select(QuoteItem)
    count_query = select(func.count(QuoteItem.id))
    
    # Filtros
    filters = []
    if search:
        search_filter = or_(
            QuoteItem.code.ilike(f"%{search}%"),
            QuoteItem.name.ilike(f"%{search}%"),
            QuoteItem.description.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if category:
        filters.append(QuoteItem.category == category)
    
    if is_active is not None:
        filters.append(QuoteItem.is_active == is_active)
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Contar total
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginación
    query = query.order_by(QuoteItem.code).offset((page - 1) * page_size).limit(page_size)
    
    # Ejecutar
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/quote-items/{item_id}", response_model=QuoteItemResponse)
async def get_quote_item(
    item_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener detalle de un concepto (solo superadmin)"""
    
    result = await db.execute(
        select(QuoteItem).where(QuoteItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Quote item not found")
    
    return item


@router.put("/quote-items/{item_id}", response_model=QuoteItemResponse)
async def update_quote_item(
    item_id: int,
    item_data: QuoteItemUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar concepto (solo superadmin)"""
    
    # Buscar concepto
    result = await db.execute(
        select(QuoteItem).where(QuoteItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Quote item not found")
    
    # Verificar código único si se actualiza
    if item_data.code and item_data.code != item.code:
        code_check = await db.execute(
            select(QuoteItem).where(QuoteItem.code == item_data.code)
        )
        if code_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Code already exists")
    
    # Actualizar campos
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    item.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(item)
    
    return item


@router.delete("/quote-items/{item_id}")
async def delete_quote_item(
    item_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Desactivar concepto (soft delete, solo superadmin)"""
    
    result = await db.execute(
        select(QuoteItem).where(QuoteItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Quote item not found")
    
    # Soft delete
    item.is_active = False
    item.updated_by = current_user.id
    
    await db.commit()
    
    return {"message": "Quote item deactivated successfully"}


@router.get("/quote-items/{item_id}/tenant-prices")
async def list_tenant_prices(
    item_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Ver precios personalizados por tenant de un concepto (solo superadmin)"""
    
    # Verificar que el concepto existe
    result = await db.execute(
        select(QuoteItem).where(QuoteItem.id == item_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Quote item not found")
    
    # Obtener precios customizados
    result = await db.execute(
        select(TenantQuoteItemPrice)
        .where(TenantQuoteItemPrice.quote_item_id == item_id)
        .order_by(TenantQuoteItemPrice.tenant_id)
    )
    prices = result.scalars().all()
    
    return prices
