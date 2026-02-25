from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class TipoDocumentoEnum(str, enum.Enum):
    ACTA_CONSTITUTIVA = "ACTA_CONSTITUTIVA"
    INE = "INE"
    IFE = "IFE"
    PODER_LEGAL = "PODER_LEGAL"
    PLANO = "PLANO"
    CONSTANCIA_SITUACION_FISCAL = "CONSTANCIA_SITUACION_FISCAL"
    COMPROBANTE_DOMICILIO = "COMPROBANTE_DOMICILIO"
    RECIBO_CFE = "RECIBO_CFE"
    CONTRATO_SUMINISTRO = "CONTRATO_SUMINISTRO"
    OTRO = "OTRO"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    tipo_documento = Column(String(50), nullable=False)  # Guardar como string en lugar de ENUM
    nombre_archivo = Column(String(500), nullable=False)
    nombre_original = Column(String(500), nullable=False)
    ruta_minio = Column(String(1000), nullable=False)
    mime_type = Column(String(100))
    tamano_bytes = Column(Integer)
    
    descripcion = Column(String(500))
    vigencia = Column(DateTime, nullable=True)  # Fecha de vencimiento del documento
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="documents")
    tenant = relationship("Tenant")
