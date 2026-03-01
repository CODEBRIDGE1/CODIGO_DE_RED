"""Company Model"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base


class TipoSuministro(str, enum.Enum):
    GDMTH = "GDMTH"  # Gran Demanda en Media Tensión Horaria
    GDMTO = "GDMTO"  # Gran Demanda en Media Tensión Ordinaria
    GDBT = "GDBT"    # Gran Demanda en Baja Tensión
    DIST = "DIST"    # Distribución


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Datos generales
    razon_social = Column(String(300), nullable=False)
    nombre_comercial = Column(String(200))
    rfc = Column(String(13), nullable=False, unique=True, index=True)
    
    # Datos de contacto
    telefono = Column(String(20))
    email = Column(String(200))
    direccion = Column(Text)
    ciudad = Column(String(100))
    estado = Column(String(100))
    codigo_postal = Column(String(10))
    
    # Datos eléctricos
    rpu = Column(String(50), nullable=True, unique=True, index=True)
    tipo_suministro = Column(String(50), nullable=True)
    tension_suministro = Column(String(50))
    
    # Demanda contratada
    demanda_contratada_kw = Column(Float)
    demanda_maxima_kw = Column(Float)
    
    # Factor de carga y potencia
    factor_carga = Column(Float)
    factor_potencia = Column(Float)
    
    # Consumo
    consumo_mensual_kwh = Column(Float)
    costo_mensual_aproximado = Column(Float)
    
    # Centro de carga
    nombre_centro_carga = Column(String(200))
    ubicacion_centro_carga = Column(Text)
    
    # Clasificación automática
    clasificacion = Column(String(50), index=True)
    
    # Notas
    notas = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    contact_phone = Column(String(50))
    status = Column(String(50), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="companies")
    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
    classification = relationship("CompanyClassification", back_populates="company", uselist=False)
    obligations = relationship("CompanyObligation", back_populates="company", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")
    evidences = relationship("Evidence", back_populates="company", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="company", cascade="all, delete-orphan")
