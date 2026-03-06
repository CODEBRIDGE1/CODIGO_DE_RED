"""
Superadmin Organization Schemas
Schemas para la información de la organización del superadmin
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class SuperadminOrganizationBase(BaseModel):
    """Schema base para organización"""
    razon_social: str = Field(..., min_length=1, max_length=300)
    nombre_comercial: Optional[str] = Field(None, max_length=200)
    rfc: str = Field(..., min_length=12, max_length=13)
    regimen_fiscal: Optional[str] = Field(None, max_length=200)
    
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    sitio_web: Optional[str] = Field(None, max_length=200)
    
    calle: Optional[str] = Field(None, max_length=200)
    numero_exterior: Optional[str] = Field(None, max_length=50)
    numero_interior: Optional[str] = Field(None, max_length=50)
    colonia: Optional[str] = Field(None, max_length=100)
    ciudad: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    pais: Optional[str] = Field("México", max_length=100)
    
    logo_url: Optional[str] = Field(None, max_length=500)
    color_primario: Optional[str] = Field(None, max_length=7)
    color_secundario: Optional[str] = Field(None, max_length=7)
    
    descripcion: Optional[str] = None
    notas_internas: Optional[str] = None
    
    @field_validator('rfc')
    @classmethod
    def validate_rfc(cls, v: str) -> str:
        """Validar formato de RFC"""
        v = v.upper().strip()
        if not re.match(r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$', v):
            raise ValueError('RFC inválido')
        return v
    
    @field_validator('color_primario', 'color_secundario')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validar formato de color hexadecimal"""
        if v is None:
            return v
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color debe estar en formato hexadecimal (#RRGGBB)')
        return v


class SuperadminOrganizationCreate(SuperadminOrganizationBase):
    """Schema para crear organización"""
    pass


class SuperadminOrganizationUpdate(BaseModel):
    """Schema para actualizar organización (todos los campos opcionales)"""
    razon_social: Optional[str] = Field(None, min_length=1, max_length=300)
    nombre_comercial: Optional[str] = Field(None, max_length=200)
    rfc: Optional[str] = Field(None, min_length=12, max_length=13)
    regimen_fiscal: Optional[str] = Field(None, max_length=200)
    
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    sitio_web: Optional[str] = Field(None, max_length=200)
    
    calle: Optional[str] = Field(None, max_length=200)
    numero_exterior: Optional[str] = Field(None, max_length=50)
    numero_interior: Optional[str] = Field(None, max_length=50)
    colonia: Optional[str] = Field(None, max_length=100)
    ciudad: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    pais: Optional[str] = Field(None, max_length=100)
    
    logo_url: Optional[str] = Field(None, max_length=500)
    color_primario: Optional[str] = Field(None, max_length=7)
    color_secundario: Optional[str] = Field(None, max_length=7)
    
    descripcion: Optional[str] = None
    notas_internas: Optional[str] = None
    
    @field_validator('rfc')
    @classmethod
    def validate_rfc(cls, v: Optional[str]) -> Optional[str]:
        """Validar formato de RFC"""
        if v is None:
            return v
        v = v.upper().strip()
        if not re.match(r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$', v):
            raise ValueError('RFC inválido')
        return v
    
    @field_validator('color_primario', 'color_secundario')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validar formato de color hexadecimal"""
        if v is None:
            return v
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color debe estar en formato hexadecimal (#RRGGBB)')
        return v


class SuperadminOrganizationResponse(SuperadminOrganizationBase):
    """Schema de respuesta para organización"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
