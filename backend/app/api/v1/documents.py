"""Document Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.models.document import Document, TipoDocumentoEnum
from app.models.company import Company
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    TipoDocumentoEnum as TipoDocumentoSchemaEnum
)
from app.core.minio_client import minio_client

router = APIRouter()


@router.post("/{company_id}/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    company_id: int,
    file: UploadFile = File(...),
    tipo_documento: str = Form(...),
    descripcion: Optional[str] = Form(None),
    vigencia: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Subir un documento al expediente de una empresa"""
    
    # Verificar que la empresa existe y pertenece al tenant del usuario
    result = await db.execute(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == current_user.tenant_id
        )
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Validar tipo de documento
    try:
        tipo_doc = TipoDocumentoEnum(tipo_documento)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipo de documento inválido: {tipo_documento}")
    
    # Generar nombre único para el archivo
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
    
    # Estructura de carpetas en MinIO: tenant_id/company_id/tipo_documento/filename
    object_name = f"tenant_{current_user.tenant_id}/company_{company_id}/{tipo_documento}/{unique_filename}"
    
    try:
        # Leer el contenido del archivo
        file_content = await file.read()
        file_size = len(file_content)
        
        # Subir a MinIO
        bucket_name = "documentos"
        minio_client.upload_file(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_content,
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Parsear vigencia si se proporciona
        vigencia_date = None
        if vigencia:
            try:
                vigencia_date = datetime.fromisoformat(vigencia.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Crear registro en la base de datos
        document = Document(
            company_id=company_id,
            tenant_id=current_user.tenant_id,
            tipo_documento=tipo_doc,
            nombre_archivo=unique_filename,
            nombre_original=file.filename,
            ruta_minio=object_name,
            mime_type=file.content_type,
            tamano_bytes=file_size,
            descripcion=descripcion,
            vigencia=vigencia_date
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Generar URL de descarga (válida por 7 días)
        download_url = minio_client.get_presigned_url(bucket_name, object_name, expires=7*24*60*60)
        
        return DocumentUploadResponse(
            message="Documento subido exitosamente",
            document_id=document.id,
            filename=file.filename,
            url=download_url
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al subir documento: {str(e)}")


@router.get("/{company_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    company_id: int,
    tipo_documento: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar documentos de una empresa"""
    
    # Verificar que la empresa existe y pertenece al tenant
    result = await db.execute(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == current_user.tenant_id
        )
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Construir query
    query = select(Document).where(
        Document.company_id == company_id,
        Document.tenant_id == current_user.tenant_id,
        Document.is_active == True
    )
    
    if tipo_documento:
        query = query.where(Document.tipo_documento == tipo_documento)
    
    query = query.order_by(Document.created_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=len(documents)
    )


@router.get("/{company_id}/documents/{document_id}/download")
async def download_document(
    company_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener URL de descarga de un documento"""
    
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.company_id == company_id,
            Document.tenant_id == current_user.tenant_id,
            Document.is_active == True
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    try:
        # Generar URL pre-firmada (válida por 1 hora)
        download_url = minio_client.get_presigned_url(
            bucket_name="documentos",
            object_name=document.ruta_minio,
            expires=60*60  # 1 hora
        )
        
        return {
            "url": download_url,
            "nombre_original": document.nombre_original,
            "mime_type": document.mime_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar URL de descarga: {str(e)}")


@router.delete("/{company_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    company_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar un documento (soft delete)"""
    
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.company_id == company_id,
            Document.tenant_id == current_user.tenant_id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Soft delete
    document.is_active = False
    await db.commit()
    
    return None
