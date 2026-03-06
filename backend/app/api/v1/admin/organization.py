"""
Superadmin Organization Router
Endpoints para gestionar la información de la organización del superadmin
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_current_superadmin, get_db
from app.models.user import User
from app.models.superadmin_organization import SuperadminOrganization
from app.schemas.superadmin_organization import (
    SuperadminOrganizationCreate,
    SuperadminOrganizationUpdate,
    SuperadminOrganizationResponse
)
from app.core.minio_client import minio_client

router = APIRouter()


@router.get("/me", response_model=SuperadminOrganizationResponse)
async def get_my_organization(
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener la información de la organización del superadmin actual"""
    
    result = await db.execute(
        select(SuperadminOrganization).where(
            SuperadminOrganization.user_id == current_user.id
        )
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=404, 
            detail="Organization not configured yet. Please create one first."
        )
    
    return organization


@router.post("/me", response_model=SuperadminOrganizationResponse, status_code=201)
async def create_my_organization(
    org_data: SuperadminOrganizationCreate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Crear la información de la organización del superadmin (solo si no existe)"""
    
    # Verificar si ya existe
    result = await db.execute(
        select(SuperadminOrganization).where(
            SuperadminOrganization.user_id == current_user.id
        )
    )
    existing_org = result.scalar_one_or_none()
    
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail="Organization already exists. Use PUT to update it."
        )
    
    # Verificar que el RFC no esté en uso
    result = await db.execute(
        select(SuperadminOrganization).where(
            SuperadminOrganization.rfc == org_data.rfc.upper()
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="RFC already registered")
    
    # Crear organización
    organization = SuperadminOrganization(
        user_id=current_user.id,
        **org_data.model_dump()
    )
    
    db.add(organization)
    await db.commit()
    await db.refresh(organization)
    
    return organization


@router.put("/me", response_model=SuperadminOrganizationResponse)
async def update_my_organization(
    org_data: SuperadminOrganizationUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar la información de la organización del superadmin"""
    
    # Buscar organización
    result = await db.execute(
        select(SuperadminOrganization).where(
            SuperadminOrganization.user_id == current_user.id
        )
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found. Use POST to create one first."
        )
    
    # Verificar RFC único si se está actualizando
    update_data = org_data.model_dump(exclude_unset=True)
    if 'rfc' in update_data and update_data['rfc']:
        rfc_upper = update_data['rfc'].upper()
        result = await db.execute(
            select(SuperadminOrganization).where(
                SuperadminOrganization.rfc == rfc_upper,
                SuperadminOrganization.id != organization.id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="RFC already registered")
        update_data['rfc'] = rfc_upper
    
    # Actualizar campos
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    await db.commit()
    await db.refresh(organization)
    
    return organization


@router.delete("/me")
async def delete_my_organization(
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar la información de la organización del superadmin"""
    
    result = await db.execute(
        select(SuperadminOrganization).where(
            SuperadminOrganization.user_id == current_user.id
        )
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    await db.delete(organization)
    await db.commit()
    
    return {"message": "Organization deleted successfully"}


@router.post("/me/logo", response_model=SuperadminOrganizationResponse)
async def upload_organization_logo(
    logo: UploadFile = File(...),
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """Subir logo de la organización del superadmin"""
    
    # Buscar organización
    result = await db.execute(
        select(SuperadminOrganization).where(
            SuperadminOrganization.user_id == current_user.id
        )
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found. Create organization first."
        )
    
    # Validar tipo de archivo
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
    content_type = logo.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Use JPG, PNG, WEBP, or SVG."
        )
    
    # Validar tamaño (max 2MB)
    contents = await logo.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 2MB limit."
        )
    
    try:
        # Subir a MinIO usando el mismo bucket de avatars
        # Usamos un prefijo para distinguirlo: org_logo_{user_id}
        logo_url = minio_client.upload_avatar(
            f"org_{current_user.id}", 
            contents, 
            content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading logo: {str(e)}"
        )
    
    # Actualizar organización con la URL del logo
    organization.logo_url = logo_url
    await db.commit()
    await db.refresh(organization)
    
    return organization
