"""Audit Log Model"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    module_key = Column(String(50), index=True)
    action = Column(String(50), index=True)
    entity_type = Column(String(50))
    entity_id = Column(Integer, nullable=True)
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    request_id = Column(String(50), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
