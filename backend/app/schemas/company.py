"""
Company Schemas - Pydantic models para empresas
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class TipoSuministroEnum(str, Enum):
    GDMTH = "GDMTH"
    GDMTO = "GDMTO"
    GDBT = "GDBT"
    DIST = "DIST"


class CompanyBase(BaseModel):
    razon_social: str = Field(..., min_length=3, max_length=300)
    nombre_comercial: Optional[str] = Field(None, max_length=200)
    rfc: str = Field(..., min_length=12, max_length=13)
    
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    
    rpu: Optional[str] = Field(None, min_length=5, max_length=50)
    tipo_suministro: Optional[TipoSuministroEnum] = None
    tension_suministro: Optional[str] = Field(None, max_length=50)
    
    demanda_contratada_kw: Optional[float] = Field(None, ge=0)
    demanda_maxima_kw: Optional[float] = Field(None, ge=0)
    factor_carga: Optional[float] = Field(None, ge=0, le=1)
    factor_potencia: Optional[float] = Field(None, ge=0, le=1)
    
    consumo_mensual_kwh: Optional[float] = Field(None, ge=0)
    costo_mensual_aproximado: Optional[float] = Field(None, ge=0)
    
    nombre_centro_carga: Optional[str] = Field(None, max_length=200)
    ubicacion_centro_carga: Optional[str] = None
    
    notas: Optional[str] = None
    is_active: bool = True

    @field_validator('rfc')
    @classmethod
    def validate_rfc(cls, v: str) -> str:
        v = v.upper().strip()
        if len(v) not in [12, 13]:
            raise ValueError('RFC debe tener 12 o 13 caracteres')
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    razon_social: Optional[str] = Field(None, min_length=3, max_length=300)
    nombre_comercial: Optional[str] = Field(None, max_length=200)
    rfc: Optional[str] = Field(None, min_length=12, max_length=13)
    
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    
    rpu: Optional[str] = Field(None, min_length=5, max_length=50)
    tipo_suministro: Optional[TipoSuministroEnum] = None
    tension_suministro: Optional[str] = Field(None, max_length=50)
    
    demanda_contratada_kw: Optional[float] = Field(None, ge=0)
    demanda_maxima_kw: Optional[float] = Field(None, ge=0)
    factor_carga: Optional[float] = Field(None, ge=0, le=1)
    factor_potencia: Optional[float] = Field(None, ge=0, le=1)
    
    consumo_mensual_kwh: Optional[float] = Field(None, ge=0)
    costo_mensual_aproximado: Optional[float] = Field(None, ge=0)
    
    nombre_centro_carga: Optional[str] = Field(None, max_length=200)
    ubicacion_centro_carga: Optional[str] = None
    
    notas: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    id: int
    tenant_id: int
    clasificacion: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    total: int
    companies: list[CompanyResponse]
    page: int
    page_size: int
