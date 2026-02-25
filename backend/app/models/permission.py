"""Permission Model"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(String(500))
    
    module = relationship("Module", back_populates="permissions")
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
