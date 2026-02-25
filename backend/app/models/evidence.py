"""Evidence Model - Simplified"""
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Evidence(Base):
    __tablename__ = "evidences"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    file_key = Column(String(500), nullable=False, unique=True, index=True)
    filename = Column(String(300), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="evidences")
    company = relationship("Company", back_populates="evidences")
