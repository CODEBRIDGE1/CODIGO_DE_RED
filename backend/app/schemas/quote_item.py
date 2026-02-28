"""
Schemas para Catálogo de Conceptos/Partidas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ============================================
# Quote Item Schemas
# ============================================

class QuoteItemBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Código único del concepto")
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del concepto")
    description: Optional[str] = Field(None, description="Descripción detallada")
    category: str = Field(..., description="Categoría del concepto")
    unit: str = Field(..., description="Unidad de medida")
    base_price: Decimal = Field(..., ge=0, description="Precio base")
    notes: Optional[str] = Field(None, description="Notas adicionales")
    is_active: bool = Field(default=True)


class QuoteItemCreate(QuoteItemBase):
    """Schema para crear concepto"""
    pass


class QuoteItemUpdate(BaseModel):
    """Schema para actualizar concepto"""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class QuoteItemResponse(QuoteItemBase):
    """Schema de respuesta con datos completos"""
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Precio efectivo para el tenant actual (puede ser custom o base)
    effective_price: Optional[Decimal] = None
    has_custom_price: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class QuoteItemListResponse(BaseModel):
    """Schema para listado paginado"""
    items: list[QuoteItemResponse]
    total: int
    page: int
    page_size: int


# ============================================
# Tenant Custom Price Schemas
# ============================================

class TenantQuoteItemPriceBase(BaseModel):
    tenant_id: int
    quote_item_id: int
    custom_price: Decimal = Field(..., ge=0, description="Precio personalizado")


class TenantQuoteItemPriceCreate(TenantQuoteItemPriceBase):
    """Schema para crear precio personalizado"""
    pass


class TenantQuoteItemPriceUpdate(BaseModel):
    """Schema para actualizar precio personalizado"""
    custom_price: Decimal = Field(..., ge=0)


class TenantQuoteItemPriceResponse(TenantQuoteItemPriceBase):
    """Schema de respuesta"""
    id: int
    created_by: int
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
