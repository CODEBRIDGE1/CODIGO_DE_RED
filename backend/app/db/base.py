"""
Base class para modelos SQLAlchemy
Import centralizado de todos los modelos para Alembic
"""
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import Column, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    """Base class para todos los modelos"""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name"""
        return cls.__name__.lower() + 's'  # Pluralizar automáticamente


# Import all models for Alembic autodiscovery (at the end to avoid circular imports)
def import_models():
    """Import models for Alembic - call this explicitly when needed"""
    from app.models import (
        tenant, license, user, role, permission, module, audit_log,
        company, obligation, project, evidence, quote, compliance, document,
        quote_item
    )


__all__ = ["Base", "import_models"]
