"""Obligation Models - Simplified for MVP"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Obligation(Base):
    __tablename__ = "obligations"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company_obligations = relationship("CompanyObligation", back_populates="obligation")

class CompanyObligation(Base):
    __tablename__ = "company_obligations"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    obligation_id = Column(Integer, ForeignKey("obligations.id"), nullable=False, index=True)
    status = Column(String(50), default="pending_review", index=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("Company", back_populates="obligations")
    obligation = relationship("Obligation", back_populates="company_obligations")
