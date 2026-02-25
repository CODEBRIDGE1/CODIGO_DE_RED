"""License Model - Licencias por tenant"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class License(Base):
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), unique=True, nullable=False, index=True)
    max_users = Column(Integer, default=10, nullable=False)
    max_storage_gb = Column(Integer, default=50, nullable=False)
    current_storage_gb = Column(Float, default=0.0, nullable=False)
    enabled_modules = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="license")
