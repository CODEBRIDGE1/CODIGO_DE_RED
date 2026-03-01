"""
Schemas para Cotizaciones
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ============================================
# Quote Line Schemas
# ============================================

class QuoteLineBase(BaseModel):
    quote_item_id: Optional[int] = Field(None, description="ID del concepto del catálogo")
    description: str = Field(..., description="Descripción del concepto")
    quantity: Decimal = Field(..., ge=0, description="Cantidad")
    unit_price: Decimal = Field(..., ge=0, description="Precio unitario")


class QuoteLineCreate(QuoteLineBase):
    """Schema para crear línea de cotización"""
    pass


class QuoteLineResponse(QuoteLineBase):
    """Schema de respuesta de línea"""
    id: int
    tenant_id: int
    quote_id: int
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# ============================================
# Quote Schemas
# ============================================

class QuoteBase(BaseModel):
    company_id: int = Field(..., description="ID de la empresa")
    title: str = Field(..., min_length=1, max_length=300, description="Título de la cotización")
    numero_transformadores: Optional[int] = Field(None, ge=0, description="Número de transformadores")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")


class QuoteCreate(QuoteBase):
    """Schema para crear cotización"""
    lines: List[QuoteLineCreate] = Field(default_factory=list, description="Líneas de cotización")


class QuoteUpdate(BaseModel):
    """Schema para actualizar cotización"""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    numero_transformadores: Optional[int] = Field(None, ge=0)
    observaciones: Optional[str] = None
    status: Optional[str] = Field(None, description="Estado de la cotización")
    lines: Optional[List[QuoteLineCreate]] = Field(None, description="Líneas de cotización actualizadas")


class QuoteResponse(QuoteBase):
    """Schema de respuesta con datos completos"""
    id: int
    tenant_id: int
    quote_number: str
    status: str
    total: Decimal
    iva_percent: Optional[int] = 0
    iva_amount: Optional[Decimal] = Decimal("0")
    total_con_iva: Optional[Decimal] = Decimal("0")
    fecha_vigencia: Optional[date] = None
    comentarios_admin: Optional[str] = None
    tipo_centro_carga: Optional[str] = None
    razon_social: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[QuoteLineResponse] = []
    
    model_config = {"from_attributes": True}


class QuoteListResponse(BaseModel):
    """Schema para lista de cotizaciones"""
    quotes: List[QuoteResponse]
    total: int
    page: int
    page_size: int
