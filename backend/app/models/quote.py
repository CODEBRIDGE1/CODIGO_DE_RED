"""Quote Models - Simplified"""
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    quote_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    status = Column(String(50), default="draft", index=True)
    total = Column(Numeric(15, 2), default=0)
    iva_percent = Column(Integer, default=16)
    iva_amount = Column(Numeric(15, 2), default=0)
    total_con_iva = Column(Numeric(15, 2), default=0)
    fecha_vigencia = Column(Date, nullable=True)
    numero_transformadores = Column(Integer)
    observaciones = Column(Text)
    comentarios_admin = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="quotes")
    company = relationship("Company", back_populates="quotes")
    lines = relationship("QuoteLine", back_populates="quote", cascade="all, delete-orphan")

class QuoteLine(Base):
    """
    Línea/partida de una cotización específica
    NOTA: Esto es diferente de QuoteItem (catálogo global en quote_item.py)
    """
    __tablename__ = "quote_lines"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, index=True)
    quote_item_id = Column(Integer, ForeignKey("quote_items.id"), nullable=True, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    quote = relationship("Quote", back_populates="lines")
