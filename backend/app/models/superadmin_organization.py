"""
Superadmin Organization Model
Información de la empresa/organización del superadmin
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class SuperadminOrganization(Base):
    """
    Información de la empresa/organización del superadmin
    Cada superadmin tiene una organización con datos fiscales, logo, etc.
    """
    __tablename__ = "superadmin_organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Datos fiscales
    razon_social = Column(String(300), nullable=False)
    nombre_comercial = Column(String(200), nullable=True)
    rfc = Column(String(13), nullable=False, unique=True, index=True)
    regimen_fiscal = Column(String(200), nullable=True)  # Ej: "601 - General de Ley Personas Morales"
    
    # Datos de contacto
    telefono = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    sitio_web = Column(String(200), nullable=True)
    
    # Dirección fiscal
    calle = Column(String(200), nullable=True)
    numero_exterior = Column(String(50), nullable=True)
    numero_interior = Column(String(50), nullable=True)
    colonia = Column(String(100), nullable=True)
    ciudad = Column(String(100), nullable=True)
    estado = Column(String(100), nullable=True)
    codigo_postal = Column(String(10), nullable=True)
    pais = Column(String(100), default="México", nullable=True)
    
    # Logo y branding
    logo_url = Column(String(500), nullable=True)
    color_primario = Column(String(7), nullable=True)  # Hex color
    color_secundario = Column(String(7), nullable=True)  # Hex color
    
    # Información adicional
    descripcion = Column(Text, nullable=True)
    notas_internas = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación con usuario superadmin
    user = relationship("User", back_populates="organization")
