"""
Tenant Model - Cliente de la plataforma SaaS
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class TenantStatus(str, enum.Enum):
    """Estados posibles del tenant"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    GRACE_PERIOD = "grace_period"
    DELETED = "deleted"


class Tenant(Base):
    """
    Tenant - Cliente de la plataforma
    Nivel superior de jerarquía multi-tenant
    """
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    subdomain = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(
        SQLEnum(TenantStatus),
        default=TenantStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Información de contacto
    contact_name = Column(String(200), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    license = relationship("License", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="tenant", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")
    evidences = relationship("Evidence", back_populates="tenant", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, subdomain={self.subdomain})>"
