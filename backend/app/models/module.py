"""Module Model"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class Module(Base):
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    icon = Column(String(50))
    shortcut_key = Column(String(1))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    permissions = relationship("Permission", back_populates="module", cascade="all, delete-orphan")
