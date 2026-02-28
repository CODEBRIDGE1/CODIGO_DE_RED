"""
Modelos para Catálogo de Conceptos/Partidas para Cotizaciones
Administrado por superadmin, usado por todos los tenants
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class ItemCategory(str, enum.Enum):
    """Categorías de conceptos"""
    INSTALACION = "INSTALACION"
    MANTENIMIENTO = "MANTENIMIENTO"
    AUDITORIA = "AUDITORIA"
    CERTIFICACION = "CERTIFICACION"
    CONSULTORIA = "CONSULTORIA"
    MATERIALES = "MATERIALES"
    MANO_OBRA = "MANO_OBRA"
    EQUIPO = "EQUIPO"
    OTRO = "OTRO"


class Unit(str, enum.Enum):
    """Unidades de medida"""
    PIEZA = "PIEZA"
    METRO = "METRO"
    METRO_CUADRADO = "METRO_CUADRADO"
    METRO_CUBICO = "METRO_CUBICO"
    SERVICIO = "SERVICIO"
    HORA = "HORA"
    DIA = "DIA"
    LOTE = "LOTE"
    KILOGRAMO = "KILOGRAMO"
    LITRO = "LITRO"


class QuoteItem(Base):
    """
    Catálogo global de conceptos/partidas para cotizaciones
    Creado y mantenido por superadmin
    """
    __tablename__ = "quote_items"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación
    code = Column(String(50), unique=True, nullable=False, index=True)  # Ej: "INS-001"
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Clasificación
    category = Column(SQLEnum(ItemCategory), nullable=False)
    unit = Column(SQLEnum(Unit), nullable=False)
    
    # Precio base (sugerido)
    base_price = Column(Numeric(10, 2), nullable=False)  # Precio base en MXN
    
    # Notas adicionales
    notes = Column(Text, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Auditoría
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    tenant_prices = relationship("TenantQuoteItemPrice", back_populates="quote_item", cascade="all, delete-orphan")


class TenantQuoteItemPrice(Base):
    """
    Precios personalizados por tenant (opcional)
    Si no existe, se usa el base_price de QuoteItem
    """
    __tablename__ = "tenant_quote_item_prices"
    __table_args__ = (
        {"sqlite_autoincrement": True, "extend_existing": True},
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    quote_item_id = Column(Integer, ForeignKey("quote_items.id"), nullable=False)
    
    # Precio ajustado para este tenant
    custom_price = Column(Numeric(10, 2), nullable=False)
    
    # Auditoría
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tenant = relationship("Tenant")
    quote_item = relationship("QuoteItem", back_populates="tenant_prices")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

