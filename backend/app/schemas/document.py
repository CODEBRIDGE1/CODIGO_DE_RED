"""Document Schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TipoDocumentoEnum(str, Enum):
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


class DocumentBase(BaseModel):
    tipo_documento: TipoDocumentoEnum
    descripcion: Optional[str] = None
    vigencia: Optional[datetime] = None


class DocumentCreate(DocumentBase):
    company_id: int
    nombre_original: str
    nombre_archivo: str
    ruta_minio: str
    mime_type: Optional[str] = None
    tamano_bytes: Optional[int] = None


class DocumentResponse(DocumentBase):
    id: int
    company_id: int
    tenant_id: int
    nombre_archivo: str
    nombre_original: str
    mime_type: Optional[str]
    tamano_bytes: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    message: str
    document_id: int
    filename: str
    url: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
