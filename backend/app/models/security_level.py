"""
SecurityLevel Model - Niveles de seguridad para usuarios tenant
Define qué módulos del sistema puede acceder un usuario.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


# Tabla de asociación SecurityLevel <-> Module
security_level_modules = Table(
    "security_level_modules",
    Base.metadata,
    Column("security_level_id", Integer, ForeignKey("security_levels.id", ondelete="CASCADE"), primary_key=True),
    Column("module_id", Integer, ForeignKey("modules.id", ondelete="CASCADE"), primary_key=True),
)


class SecurityLevel(Base):
    """
    Nivel de seguridad - define los módulos accesibles para un usuario.
    Gestionado por el superadmin, asignado a usuarios de tenant.
    """
    __tablename__ = "security_levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    color = Column(String(20), default="blue", nullable=False)  # Para UI: blue, green, red, yellow, purple, gray
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Módulos accesibles para este nivel
    modules = relationship(
        "Module",
        secondary=security_level_modules,
        lazy="selectin"
    )

    # Usuarios que tienen este nivel
    users = relationship("User", back_populates="security_level")

    def __repr__(self) -> str:
        return f"<SecurityLevel(id={self.id}, name={self.name})>"
