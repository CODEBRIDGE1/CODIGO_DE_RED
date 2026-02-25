"""Modelos para Matriz de Obligaciones"""
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class TipoCentroCarga(str, enum.Enum):
    """Tipos de centro de carga según demanda y tensión"""
    TIPO_A = "TIPO_A"  # Media Tensión con demanda < 1 MW
    TIPO_B = "TIPO_B"  # Media Tensión con demanda >= 1 MW
    TIPO_C = "TIPO_C"  # Alta Tensión


class EstadoAplicabilidad(str, enum.Enum):
    """Estados de aplicabilidad de un requerimiento"""
    APLICA = "APLICA"
    NO_APLICA = "NO_APLICA"
    APLICA_RDC = "APLICA_RDC"  # Aplica solo para RDC
    APLICA_TIC = "APLICA_TIC"  # Aplica conforme Manual TIC


class CompanyClassification(Base):
    """Clasificación de tipo de centro de carga por empresa"""
    __tablename__ = "company_classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    tipo_centro_carga = Column(SQLEnum(TipoCentroCarga), nullable=False)
    
    # Justificación de la clasificación
    justificacion = Column(Text, nullable=True)
    
    # Auditoría
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    company = relationship("Company", back_populates="classification")
    tenant = relationship("Tenant")
    creator = relationship("User", foreign_keys=[created_by])


class ComplianceRequirement(Base):
    """Catálogo de requerimientos de la Tabla 1.1.A"""
    __tablename__ = "compliance_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Código del requerimiento (ej: "2.1", "2.8.1")
    codigo = Column(String(20), nullable=False, unique=True, index=True)
    
    # Nombre del requerimiento
    nombre = Column(String(200), nullable=False)
    
    # Descripción detallada
    descripcion = Column(Text, nullable=True)
    
    # Jerarquía: si es hijo de otro requerimiento
    parent_id = Column(Integer, ForeignKey("compliance_requirements.id"), nullable=True)
    
    # Orden de visualización
    orden = Column(Integer, nullable=False, default=0)
    
    # Activo/Inactivo
    is_active = Column(Boolean, default=True)
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    parent = relationship("ComplianceRequirement", remote_side=[id], backref="children")
    rules = relationship("ComplianceRule", back_populates="requirement")


class ComplianceRule(Base):
    """Matriz de aplicabilidad: qué requerimientos aplican a cada tipo"""
    __tablename__ = "compliance_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    requirement_id = Column(Integer, ForeignKey("compliance_requirements.id"), nullable=False)
    tipo_centro_carga = Column(SQLEnum(TipoCentroCarga), nullable=False)
    estado_aplicabilidad = Column(SQLEnum(EstadoAplicabilidad), nullable=False)
    
    # Notas adicionales sobre la aplicabilidad
    notas = Column(Text, nullable=True)
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    requirement = relationship("ComplianceRequirement", back_populates="rules")
    
    # Unique constraint: un requerimiento solo tiene una regla por tipo
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class ComplianceAuditLog(Base):
    """Bitácora de cambios en clasificaciones y cumplimiento"""
    __tablename__ = "compliance_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Tipo de acción
    action_type = Column(String(50), nullable=False)  # CLASSIFICATION_CREATED, CLASSIFICATION_UPDATED, etc.
    
    # IDs relacionados
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Datos del cambio
    old_value = Column(Text, nullable=True)  # JSON con valor anterior
    new_value = Column(Text, nullable=True)  # JSON con valor nuevo
    
    # Usuario que realizó la acción
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    company = relationship("Company")
    tenant = relationship("Tenant")
    user = relationship("User")
