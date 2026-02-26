"""
API endpoints for Compliance Matrix (Matriz de Obligaciones)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, cast, String
from typing import List
import json

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.company import Company
from app.models.compliance import (
    CompanyClassification,
    ComplianceRequirement,
    ComplianceRule,
    ComplianceAuditLog,
    TipoCentroCarga,
    EstadoAplicabilidad
)
from app.schemas.compliance import (
    CompanyClassificationCreate,
    CompanyClassificationUpdate,
    CompanyClassificationResponse,
    ComplianceRequirementResponse,
    ComplianceRuleResponse,
    ComplianceMatrixResponse,
    ComplianceMatrixItem,
    ComplianceAuditLogResponse,
    TipoCentroCargaEnum,
    EstadoAplicabilidadEnum
)

router = APIRouter()


# === ENDPOINTS FOR TENANTS ===

@router.post("/companies/{company_id}/classification", response_model=CompanyClassificationResponse)
async def create_company_classification(
    company_id: int,
    classification: CompanyClassificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crear clasificación de tipo de centro de carga para una empresa"""
    
    # Verificar que la empresa existe y pertenece al tenant
    result = await db.execute(
        select(Company).where(
            and_(
                Company.id == company_id,
                Company.tenant_id == current_user.tenant_id
            )
        )
    )
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Verificar si ya existe una clasificación
    result = await db.execute(
        select(CompanyClassification).where(
            CompanyClassification.company_id == company_id
        )
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Company already has a classification. Use PUT to update."
        )
    
    # Crear clasificación
    db_classification = CompanyClassification(
        company_id=company_id,
        tenant_id=current_user.tenant_id,
        tipo_centro_carga=classification.tipo_centro_carga,
        justificacion=classification.justificacion,
        created_by=current_user.id
    )
    db.add(db_classification)
    
    # Registrar en audit log
    audit = ComplianceAuditLog(
        action_type="CREATE_CLASSIFICATION",
        company_id=company_id,
        tenant_id=current_user.tenant_id,
        old_value=None,
        new_value=json.dumps({
            "tipo_centro_carga": classification.tipo_centro_carga.value,
            "justificacion": classification.justificacion
        }),
        user_id=current_user.id
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(db_classification)
    
    return db_classification


@router.put("/companies/{company_id}/classification", response_model=CompanyClassificationResponse)
async def update_company_classification(
    company_id: int,
    classification: CompanyClassificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar clasificación de tipo de centro de carga"""
    
    # Verificar que la empresa existe y pertenece al tenant
    result = await db.execute(
        select(Company).where(
            and_(
                Company.id == company_id,
                Company.tenant_id == current_user.tenant_id
            )
        )
    )
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Obtener clasificación existente
    result = await db.execute(
        select(CompanyClassification).where(
            CompanyClassification.company_id == company_id
        )
    )
    db_classification = result.scalars().first()
    if not db_classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    # Guardar valores anteriores para audit
    old_value = {
        "tipo_centro_carga": db_classification.tipo_centro_carga.value,
        "justificacion": db_classification.justificacion
    }
    
    # Actualizar
    if classification.tipo_centro_carga is not None:
        db_classification.tipo_centro_carga = classification.tipo_centro_carga
    if classification.justificacion is not None:
        db_classification.justificacion = classification.justificacion
    
    # Registrar en audit log
    new_value = {
        "tipo_centro_carga": db_classification.tipo_centro_carga.value,
        "justificacion": db_classification.justificacion
    }
    audit = ComplianceAuditLog(
        action_type="UPDATE_CLASSIFICATION",
        company_id=company_id,
        tenant_id=current_user.tenant_id,
        old_value=json.dumps(old_value),
        new_value=json.dumps(new_value),
        user_id=current_user.id
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(db_classification)
    
    return db_classification


@router.get("/companies/{company_id}/classification", response_model=CompanyClassificationResponse)
async def get_company_classification(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener clasificación de una empresa"""
    
    # Verificar que la empresa pertenece al tenant
    result = await db.execute(
        select(Company).where(
            and_(
                Company.id == company_id,
                Company.tenant_id == current_user.tenant_id
            )
        )
    )
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    result = await db.execute(
        select(CompanyClassification).where(
            CompanyClassification.company_id == company_id
        )
    )
    classification = result.scalars().first()
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    return classification


@router.get("/companies/{company_id}/compliance-matrix", response_model=ComplianceMatrixResponse)
async def get_company_compliance_matrix(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener matriz de cumplimiento completa para una empresa"""
    
    # Verificar empresa y obtener clasificación
    result = await db.execute(
        select(Company, CompanyClassification).join(
            CompanyClassification,
            Company.id == CompanyClassification.company_id
        ).where(
            and_(
                Company.id == company_id,
                Company.tenant_id == current_user.tenant_id
            )
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Company or classification not found"
        )
    
    company, classification = row
    
    # Obtener todos los requerimientos (solo padres, hijos vendrán recursivamente)
    result = await db.execute(
        select(ComplianceRequirement).where(
            and_(
                ComplianceRequirement.is_active == True,
                ComplianceRequirement.parent_id == None
            )
        ).order_by(ComplianceRequirement.orden)
    )
    requirements = result.scalars().all()
    
    # Obtener todas las reglas para este tipo
    # Comparar usando cast para evitar problemas de tipo enum
    tipo_carga_str = classification.tipo_centro_carga.value if hasattr(classification.tipo_centro_carga, 'value') else str(classification.tipo_centro_carga)
    
    result = await db.execute(
        select(ComplianceRule).where(
            cast(ComplianceRule.tipo_centro_carga, String) == tipo_carga_str
        )
    )
    rules = result.scalars().all()
    rules_dict = {rule.requirement_id: rule for rule in rules}
    
    # Construir matriz recursivamente
    async def build_requirement_tree(req: ComplianceRequirement) -> ComplianceMatrixItem:
        rule = rules_dict.get(req.id)
        
        # Obtener hijos
        result = await db.execute(
            select(ComplianceRequirement).where(
                and_(
                    ComplianceRequirement.parent_id == req.id,
                    ComplianceRequirement.is_active == True
                )
            ).order_by(ComplianceRequirement.orden)
        )
        children_reqs = result.scalars().all()
        children = [await build_requirement_tree(child) for child in children_reqs]
        
        return ComplianceMatrixItem(
            requerimiento_id=req.id,
            codigo=req.codigo,
            nombre=req.nombre,
            descripcion=req.descripcion,
            parent_id=req.parent_id,
            orden=req.orden,
            estado_aplicabilidad=rule.estado_aplicabilidad if rule else EstadoAplicabilidadEnum.NO_APLICA,
            notas=rule.notas if rule else None,
            children=children
        )
    
    requerimientos = [await build_requirement_tree(req) for req in requirements]
    
    return ComplianceMatrixResponse(
        company_id=company.id,
        razon_social=company.razon_social,
        tipo_centro_carga=classification.tipo_centro_carga,
        requerimientos=requerimientos
    )


# === ADMIN ENDPOINTS ===

@router.get("/admin/requirements", response_model=List[ComplianceRequirementResponse])
async def get_all_requirements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener catálogo completo de requerimientos (solo admin)"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(
        select(ComplianceRequirement).where(
            ComplianceRequirement.parent_id == None
        ).order_by(ComplianceRequirement.orden)
    )
    requirements = result.scalars().all()
    
    async def build_tree(req: ComplianceRequirement) -> ComplianceRequirementResponse:
        result = await db.execute(
            select(ComplianceRequirement).where(
                ComplianceRequirement.parent_id == req.id
            ).order_by(ComplianceRequirement.orden)
        )
        children_reqs = result.scalars().all()
        children = [await build_tree(child) for child in children_reqs]
        
        return ComplianceRequirementResponse(
            id=req.id,
            codigo=req.codigo,
            nombre=req.nombre,
            descripcion=req.descripcion,
            parent_id=req.parent_id,
            orden=req.orden,
            is_active=req.is_active,
            children=children
        )
    
    return [await build_tree(req) for req in requirements]


@router.get("/admin/rules", response_model=List[ComplianceRuleResponse])
async def get_all_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener todas las reglas de aplicabilidad (solo admin)"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(ComplianceRule))
    rules = result.scalars().all()
    
    return rules


@router.get("/audit-log", response_model=List[ComplianceAuditLogResponse])
async def get_audit_log(
    company_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener bitácora de cambios en clasificaciones"""
    
    query = select(ComplianceAuditLog).where(
        ComplianceAuditLog.tenant_id == current_user.tenant_id
    )
    
    if company_id:
        query = query.where(ComplianceAuditLog.company_id == company_id)
    
    query = query.order_by(ComplianceAuditLog.created_at.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs
