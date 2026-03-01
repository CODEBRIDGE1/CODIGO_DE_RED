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
    ComplianceRequirementCreate,
    ComplianceRequirementUpdate,
    ComplianceRuleResponse,
    ComplianceRuleCreate,
    ComplianceRuleUpdate,
    ComplianceMatrixResponse,
    ComplianceMatrixItem,
    ComplianceAuditLogResponse,
    TipoCentroCargaEnum,
    EstadoAplicabilidadEnum
)
from app.schemas.company import CompanySlimResponse
from typing import List as TypingList

router = APIRouter()


# === ENDPOINTS FOR TENANTS ===

@router.get("/companies/", response_model=TypingList[CompanySlimResponse])
async def list_companies_slim(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista slim de empresas del tenant con su clasificación (si existe).
    Solo devuelve los campos necesarios para la Matriz de Obligaciones:
    id, razon_social, rfc, is_active, tipo_centro_carga, justificacion.
    """
    result = await db.execute(
        select(Company, CompanyClassification)
        .outerjoin(CompanyClassification, CompanyClassification.company_id == Company.id)
        .where(Company.tenant_id == current_user.tenant_id)
        .order_by(Company.razon_social.asc())
    )
    rows = result.all()

    items = []
    for company, classification in rows:
        items.append(CompanySlimResponse(
            id=company.id,
            razon_social=company.razon_social,
            rfc=company.rfc,
            is_active=company.is_active,
            tipo_centro_carga=classification.tipo_centro_carga.value if classification and classification.tipo_centro_carga else None,
            justificacion=classification.justificacion if classification else None,
        ))
    return items


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
            created_at=req.created_at,
            updated_at=req.updated_at,
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


# === ADMIN CRUD ENDPOINTS FOR REQUIREMENTS ===

@router.post("/admin/requirements", response_model=ComplianceRequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    requirement: ComplianceRequirementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crear nuevo requerimiento de compliance (solo admin)"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validar que el parent existe si se especifica
    if requirement.parent_id:
        result = await db.execute(
            select(ComplianceRequirement).where(ComplianceRequirement.id == requirement.parent_id)
        )
        parent = result.scalars().first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent requirement not found")
    
    # Crear requerimiento
    db_requirement = ComplianceRequirement(**requirement.model_dump())
    db.add(db_requirement)
    await db.commit()
    await db.refresh(db_requirement)
    
    # Cargar children vacío
    db_requirement.children = []
    
    return db_requirement


@router.put("/admin/requirements/{requirement_id}", response_model=ComplianceRequirementResponse)
async def update_requirement(
    requirement_id: int,
    requirement: ComplianceRequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar requerimiento existente (solo admin)"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Obtener requerimiento
    result = await db.execute(
        select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id)
    )
    db_requirement = result.scalars().first()
    if not db_requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # Validar parent si se especifica
    if requirement.parent_id is not None:
        if requirement.parent_id == requirement_id:
            raise HTTPException(status_code=400, detail="Requirement cannot be its own parent")
        result = await db.execute(
            select(ComplianceRequirement).where(ComplianceRequirement.id == requirement.parent_id)
        )
        parent = result.scalars().first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent requirement not found")
    
    # Actualizar campos
    update_data = requirement.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_requirement, field, value)
    
    await db.commit()
    await db.refresh(db_requirement)
    
    # Cargar children
    result = await db.execute(
        select(ComplianceRequirement).where(ComplianceRequirement.parent_id == db_requirement.id)
    )
    db_requirement.children = result.scalars().all()
    
    return db_requirement


@router.delete("/admin/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar requerimiento (solo admin)"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Obtener requerimiento
    result = await db.execute(
        select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id)
    )
    db_requirement = result.scalars().first()
    if not db_requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # Verificar que no tenga hijos
    result = await db.execute(
        select(ComplianceRequirement).where(ComplianceRequirement.parent_id == requirement_id)
    )
    children = result.scalars().all()
    if children:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete requirement with children. Delete children first."
        )
    
    # Eliminar reglas asociadas
    await db.execute(
        select(ComplianceRule).where(ComplianceRule.requirement_id == requirement_id)
    )
    
    await db.delete(db_requirement)
    await db.commit()


# === ADMIN CRUD ENDPOINTS FOR RULES ===

@router.post("/admin/rules", response_model=ComplianceRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule: ComplianceRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crear nueva regla de aplicabilidad (solo admin)"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validar que el requirement existe
    result = await db.execute(
        select(ComplianceRequirement).where(ComplianceRequirement.id == rule.requirement_id)
    )
    requirement = result.scalars().first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # Verificar que no exista ya una regla para este requirement + tipo
    result = await db.execute(
        select(ComplianceRule).where(
            and_(
                ComplianceRule.requirement_id == rule.requirement_id,
                cast(ComplianceRule.tipo_centro_carga, String) == rule.tipo_centro_carga.value
            )
        )
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Rule already exists for this requirement and tipo_centro_carga"
        )
    
    # Crear regla
    db_rule = ComplianceRule(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    
    return db_rule


@router.put("/admin/rules/{rule_id}", response_model=ComplianceRuleResponse)
async def update_rule(
    rule_id: int,
    rule: ComplianceRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar regla existente (solo admin)"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Obtener regla
    result = await db.execute(
        select(ComplianceRule).where(ComplianceRule.id == rule_id)
    )
    db_rule = result.scalars().first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Actualizar campos
    update_data = rule.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    await db.commit()
    await db.refresh(db_rule)
    
    return db_rule


@router.delete("/admin/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar regla (solo admin)"""
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Obtener regla
    result = await db.execute(
        select(ComplianceRule).where(ComplianceRule.id == rule_id)
    )
    db_rule = result.scalars().first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(db_rule)
    await db.commit()
