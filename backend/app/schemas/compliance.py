"""Schemas para Matriz de Obligaciones"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TipoCentroCargaEnum(str, Enum):
    """Tipos de centro de carga"""
    TIPO_A = "TIPO_A"  # Media Tensión con demanda < 1 MW
    TIPO_B = "TIPO_B"  # Media Tensión con demanda >= 1 MW
    TIPO_C = "TIPO_C"  # Alta Tensión


class EstadoAplicabilidadEnum(str, Enum):
    """Estados de aplicabilidad"""
    APLICA = "APLICA"
    NO_APLICA = "NO_APLICA"
    APLICA_RDC = "APLICA_RDC"
    APLICA_TIC = "APLICA_TIC"


# Company Classification Schemas
class CompanyClassificationCreate(BaseModel):
    """Schema for creating company classification (company_id comes from URL path)"""
    tipo_centro_carga: TipoCentroCargaEnum
    justificacion: Optional[str] = None


class CompanyClassificationUpdate(BaseModel):
    """Schema for updating company classification"""
    tipo_centro_carga: Optional[TipoCentroCargaEnum] = None
    justificacion: Optional[str] = None


class CompanyClassificationResponse(BaseModel):
    """Schema for company classification response"""
    id: int
    company_id: int
    tenant_id: int
    tipo_centro_carga: TipoCentroCargaEnum
    justificacion: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Compliance Requirement Schemas
class ComplianceRequirementBase(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    parent_id: Optional[int] = None
    orden: int = 0
    is_active: bool = True


class ComplianceRequirementCreate(ComplianceRequirementBase):
    pass


class ComplianceRequirementUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    parent_id: Optional[int] = None
    orden: Optional[int] = None
    is_active: Optional[bool] = None


class ComplianceRequirementResponse(ComplianceRequirementBase):
    id: int
    created_at: datetime
    updated_at: datetime
    children: List['ComplianceRequirementResponse'] = []
    
    class Config:
        from_attributes = True


# Compliance Rule Schemas
class ComplianceRuleBase(BaseModel):
    requirement_id: int
    tipo_centro_carga: TipoCentroCargaEnum
    estado_aplicabilidad: EstadoAplicabilidadEnum
    notas: Optional[str] = None


class ComplianceRuleCreate(ComplianceRuleBase):
    pass


class ComplianceRuleUpdate(BaseModel):
    estado_aplicabilidad: Optional[EstadoAplicabilidadEnum] = None
    notas: Optional[str] = None


class ComplianceRuleResponse(ComplianceRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Compliance Matrix Response (Combined view)
class ComplianceMatrixItem(BaseModel):
    """Item de la matriz con requerimiento y su aplicabilidad"""
    requerimiento_id: int
    codigo: str
    nombre: str
    descripcion: Optional[str]
    parent_id: Optional[int]
    orden: int
    estado_aplicabilidad: EstadoAplicabilidadEnum
    notas: Optional[str]
    children: List['ComplianceMatrixItem'] = []
    
    class Config:
        from_attributes = True


class ComplianceMatrixResponse(BaseModel):
    """Matriz completa para una empresa"""
    company_id: int
    razon_social: str
    tipo_centro_carga: TipoCentroCargaEnum
    requerimientos: List[ComplianceMatrixItem]


# Audit Log Schemas
class ComplianceAuditLogResponse(BaseModel):
    id: int
    action_type: str
    company_id: Optional[int]
    tenant_id: int
    old_value: Optional[str]
    new_value: Optional[str]
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
