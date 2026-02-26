"""
API endpoints for Projects (Proyectos)
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, cast, String
from typing import List, Optional
import json
from datetime import datetime

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.company import Company
from app.models.compliance import CompanyClassification, ComplianceRequirement, ComplianceRule
from app.models.project import (
    Project, ProjectTask, TaskEvidence, TaskComment, TaskActivityLog,
    ProjectStatus, TaskStatus, TaskType
)
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListItem, ProjectDetail,
    TaskCreate, TaskUpdate, TaskResponse, TaskSummary,
    EvidenceCreate, EvidenceResponse,
    CommentCreate, CommentResponse,
    ActivityLogResponse,
    ProjectMetrics, TaskMetrics
)
from app.core.minio_client import minio_client

router = APIRouter()


# =======================
# PROJECT ENDPOINTS
# =======================

@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear proyecto vinculado a una empresa.
    Automáticamente crea tareas basadas en obligaciones aplicables.
    """
    
    # Verificar que la empresa existe y pertenece al tenant
    result = await db.execute(
        select(Company, CompanyClassification).outerjoin(
            CompanyClassification,
            Company.id == CompanyClassification.company_id
        ).where(
            and_(
                Company.id == project_data.company_id,
                Company.tenant_id == current_user.tenant_id
            )
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company, classification = row
    
    if not classification:
        raise HTTPException(
            status_code=400,
            detail="Company must be classified before creating a project"
        )
    
    # Crear proyecto
    db_project = Project(
        tenant_id=current_user.tenant_id,
        company_id=project_data.company_id,
        name=project_data.name,
        description=project_data.description,
        project_type=project_data.project_type,
        priority=project_data.priority,
        start_date=project_data.start_date,
        due_date=project_data.due_date,
        created_by=current_user.id
    )
    db.add(db_project)
    await db.flush()  # Para obtener el ID
    
    # Obtener obligaciones aplicables según clasificación
    tipo_carga_str = classification.tipo_centro_carga.value if hasattr(classification.tipo_centro_carga, 'value') else str(classification.tipo_centro_carga)
    
    result = await db.execute(
        select(ComplianceRule, ComplianceRequirement).join(
            ComplianceRequirement,
            ComplianceRule.requirement_id == ComplianceRequirement.id
        ).where(
            and_(
                cast(ComplianceRule.tipo_centro_carga, String) == tipo_carga_str,
                ComplianceRule.estado_aplicabilidad != 'NO_APLICA',
                ComplianceRequirement.is_active == True
            )
        ).order_by(ComplianceRequirement.orden)
    )
    applicable_rules = result.all()
    
    # Crear tareas según selección
    tasks_to_create = []
    sort_order = 0
    
    if project_data.include_all_obligations:
        # Incluir todas las obligaciones aplicables
        for rule, requirement in applicable_rules:
            tasks_to_create.append(ProjectTask(
                project_id=db_project.id,
                task_type=TaskType.OBLIGATION,
                requirement_id=requirement.id,
                code=requirement.codigo,
                title=requirement.nombre,
                description=requirement.descripcion,
                notes=rule.notas,
                sort_order=sort_order,
                created_by=current_user.id
            ))
            sort_order += 1
    else:
        # Incluir solo obligaciones seleccionadas
        if project_data.selected_requirement_ids:
            applicable_ids = {req.id for _, req in applicable_rules}
            for rule, requirement in applicable_rules:
                if requirement.id in project_data.selected_requirement_ids:
                    tasks_to_create.append(ProjectTask(
                        project_id=db_project.id,
                        task_type=TaskType.OBLIGATION,
                        requirement_id=requirement.id,
                        code=requirement.codigo,
                        title=requirement.nombre,
                        description=requirement.descripcion,
                        notes=rule.notas,
                        sort_order=sort_order,
                        created_by=current_user.id
                    ))
                    sort_order += 1
    
    # Agregar tareas custom
    if project_data.custom_tasks:
        for custom_task in project_data.custom_tasks:
            tasks_to_create.append(ProjectTask(
                project_id=db_project.id,
                task_type=TaskType.CUSTOM,
                code=custom_task.code,
                title=custom_task.title,
                description=custom_task.description,
                sort_order=sort_order,
                created_by=current_user.id
            ))
            sort_order += 1
    
    # Guardar tareas
    for task in tasks_to_create:
        db.add(task)
    
    await db.commit()
    await db.refresh(db_project)
    
    return db_project


@router.get("/", response_model=List[ProjectListItem])
async def list_projects(
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    project_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Listar proyectos del tenant con filtros opcionales"""
    
    query = select(Project, Company).join(
        Company, Project.company_id == Company.id
    ).where(
        Project.tenant_id == current_user.tenant_id
    )
    
    if company_id:
        query = query.where(Project.company_id == company_id)
    if status:
        query = query.where(cast(Project.status, String) == status)
    if project_type:
        query = query.where(cast(Project.project_type, String) == project_type)
    
    query = query.order_by(Project.created_at.desc())
    
    result = await db.execute(query)
    projects_data = result.all()
    
    # Construir respuesta con métricas
    response = []
    for project, company in projects_data:
        # Calcular métricas
        metrics_result = await db.execute(
            select(
                func.count(ProjectTask.id).label('total'),
                func.count().filter(ProjectTask.status == TaskStatus.COMPLETADO).label('completed'),
                func.count().filter(ProjectTask.status == TaskStatus.EN_PROGRESO).label('in_progress'),
                func.count().filter(ProjectTask.status == TaskStatus.NO_INICIADO).label('not_started'),
                func.count().filter(ProjectTask.status == TaskStatus.CERRADO).label('closed'),
            ).where(ProjectTask.project_id == project.id)
        )
        metrics_row = metrics_result.first()
        
        # Contar evidencias
        evidence_count_result = await db.execute(
            select(func.count(TaskEvidence.id)).join(
                ProjectTask, TaskEvidence.task_id == ProjectTask.id
            ).where(ProjectTask.project_id == project.id)
        )
        evidence_count = evidence_count_result.scalar() or 0
        
        total_tasks = metrics_row.total or 0
        completed = metrics_row.completed or 0
        
        metrics = TaskMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed,
            in_progress_tasks=metrics_row.in_progress or 0,
            not_started_tasks=metrics_row.not_started or 0,
            closed_tasks=metrics_row.closed or 0,
            completion_percentage=round((completed / total_tasks * 100) if total_tasks > 0 else 0, 2),
            total_evidences=evidence_count
        )
        
        response.append(ProjectListItem(
            id=project.id,
            company_id=project.company_id,
            company_name=company.razon_social,
            name=project.name,
            description=project.description,
            project_type=project.project_type,
            status=project.status,
            priority=project.priority,
            start_date=project.start_date,
            due_date=project.due_date,
            created_at=project.created_at,
            metrics=metrics
        ))
    
    return response


@router.get("/{project_id}/available-obligations")
async def get_available_obligations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Listar obligaciones disponibles para agregar a un proyecto.
    Retorna las que aplican a la empresa del proyecto, excluyendo las ya agregadas.
    """
    # Obtener proyecto y su empresa
    result = await db.execute(
        select(Project).where(
            and_(Project.id == project_id, Project.tenant_id == current_user.tenant_id)
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Obtener clasificación de la empresa
    classif_result = await db.execute(
        select(CompanyClassification).where(CompanyClassification.company_id == project.company_id)
    )
    classification = classif_result.scalars().first()

    # Obtener IDs de obligaciones ya en el proyecto
    existing_result = await db.execute(
        select(ProjectTask.requirement_id).where(
            and_(
                ProjectTask.project_id == project_id,
                ProjectTask.requirement_id.isnot(None)
            )
        )
    )
    existing_ids = {row[0] for row in existing_result.all()}

    # Buscar obligaciones aplicables (join correcto: ComplianceRule referencia a ComplianceRequirement)
    req_query = (
        select(ComplianceRequirement, ComplianceRule)
        .join(ComplianceRule, ComplianceRule.requirement_id == ComplianceRequirement.id)
        .where(ComplianceRequirement.is_active == True)
    )

    if classification:
        req_query = req_query.where(
            and_(
                ComplianceRule.tipo_centro_carga == classification.tipo_centro_carga,
                ComplianceRule.estado_aplicabilidad != "NO_APLICA"
            )
        )

    req_result = await db.execute(req_query)
    rows = req_result.all()

    obligations = []
    for req, rule in rows:
        if req.id not in existing_ids:
            obligations.append({
                "id": req.id,
                "codigo": req.codigo,
                "nombre": req.nombre,
                "descripcion": req.descripcion or "",
                "estado_aplicabilidad": rule.estado_aplicabilidad,
                "notas": rule.notas or "",
            })

    # Ordenar por código
    obligations.sort(key=lambda x: x["codigo"])

    return {"obligations": obligations, "total": len(obligations), "classified": classification is not None}


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener detalle de proyecto con todas sus tareas"""
    
    # Obtener proyecto
    result = await db.execute(
        select(Project, Company).join(
            Company, Project.company_id == Company.id
        ).where(
            and_(
                Project.id == project_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project, company = row
    
    # Obtener tareas con información del asignado
    tasks_result = await db.execute(
        select(ProjectTask, User).outerjoin(
            User, ProjectTask.assignee_user_id == User.id
        ).where(
            ProjectTask.project_id == project_id
        ).order_by(ProjectTask.sort_order)
    )
    task_rows = tasks_result.all()
    
    # Calcular métricas
    metrics_result = await db.execute(
        select(
            func.count(ProjectTask.id).label('total'),
            func.count().filter(ProjectTask.status == TaskStatus.COMPLETADO).label('completed'),
            func.count().filter(ProjectTask.status == TaskStatus.EN_PROGRESO).label('in_progress'),
            func.count().filter(ProjectTask.status == TaskStatus.NO_INICIADO).label('not_started'),
            func.count().filter(ProjectTask.status == TaskStatus.CERRADO).label('closed'),
        ).where(ProjectTask.project_id == project.id)
    )
    metrics_row = metrics_result.first()
    
    evidence_count_result = await db.execute(
        select(func.count(TaskEvidence.id)).join(
            ProjectTask, TaskEvidence.task_id == ProjectTask.id
        ).where(ProjectTask.project_id == project.id)
    )
    evidence_count = evidence_count_result.scalar() or 0
    
    total_tasks = metrics_row.total or 0
    completed = metrics_row.completed or 0
    
    metrics = TaskMetrics(
        total_tasks=total_tasks,
        completed_tasks=completed,
        in_progress_tasks=metrics_row.in_progress or 0,
        not_started_tasks=metrics_row.not_started or 0,
        closed_tasks=metrics_row.closed or 0,
        completion_percentage=round((completed / total_tasks * 100) if total_tasks > 0 else 0, 2),
        total_evidences=evidence_count
    )
    
    # Construir lista de tareas con conteo de evidencias
    task_summaries = []
    for task, assignee in task_rows:
        evidence_count_result = await db.execute(
            select(func.count(TaskEvidence.id)).where(TaskEvidence.task_id == task.id)
        )
        task_evidence_count = evidence_count_result.scalar() or 0
        
        task_summaries.append(TaskSummary(
            id=task.id,
            code=task.code,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status=task.status,
            assignee_user_id=task.assignee_user_id,
            assignee_name=f"{assignee.first_name} {assignee.last_name}" if assignee else None,
            due_date=task.due_date,
            progress_percentage=task.progress_percentage,
            evidence_count=task_evidence_count
        ))
    
    return ProjectDetail(
        id=project.id,
        tenant_id=project.tenant_id,
        company_id=project.company_id,
        company_name=company.razon_social,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        priority=project.priority,
        start_date=project.start_date,
        due_date=project.due_date,
        completed_at=project.completed_at,
        closed_at=project.closed_at,
        created_at=project.created_at,
        updated_at=project.updated_at,
        tasks=task_summaries,
        total_tasks=metrics.total_tasks,
        completed_tasks=metrics.completed_tasks,
        progress_percentage=int(metrics.completion_percentage)
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar metadatos de un proyecto"""
    
    result = await db.execute(
        select(Project).where(
            and_(
                Project.id == project_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Actualizar campos
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.post("/{project_id}/close", response_model=ProjectResponse)
async def close_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cerrar un proyecto"""
    
    result = await db.execute(
        select(Project).where(
            and_(
                Project.id == project_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.status = ProjectStatus.CERRADO
    project.closed_at = datetime.utcnow()
    project.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(project)
    
    return project


# =======================
# TASK ENDPOINTS
# =======================

@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    project_id: int,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crear tarea adicional en un proyecto (custom o obligación adicional)"""
    
    # Verificar proyecto
    result = await db.execute(
        select(Project).where(
            and_(
                Project.id == project_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Obtener siguiente sort_order
    sort_order_result = await db.execute(
        select(func.max(ProjectTask.sort_order)).where(ProjectTask.project_id == project_id)
    )
    max_order = sort_order_result.scalar() or 0
    
    # Crear tarea
    db_task = ProjectTask(
        project_id=project_id,
        task_type=task_data.task_type,
        requirement_id=task_data.requirement_id,
        title=task_data.title,
        description=task_data.description,
        notes=task_data.notes,
        assignee_user_id=task_data.assignee_user_id,
        due_date=task_data.due_date,
        sort_order=max_order + 1,
        created_by=current_user.id
    )
    db.add(db_task)
    await db.flush()
    
    # Log de actividad
    activity_log = TaskActivityLog(
        task_id=db_task.id,
        event_type="TASK_CREATED",
        payload_json=json.dumps({"title": task_data.title}),
        created_by=current_user.id
    )
    db.add(activity_log)
    
    await db.commit()
    await db.refresh(db_task)
    
    return db_task


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener detalle de una tarea"""
    
    result = await db.execute(
        select(ProjectTask).join(
            Project, ProjectTask.project_id == Project.id
        ).where(
            and_(
                ProjectTask.id == task_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar tarea (status, assignee, etc.)"""
    
    result = await db.execute(
        select(ProjectTask).join(
            Project, ProjectTask.project_id == Project.id
        ).where(
            and_(
                ProjectTask.id == task_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Registrar cambios en actividad
    old_status = task.status
    
    # Actualizar campos
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    task.updated_by = current_user.id
    
    # Log si cambió el status
    if 'status' in update_data and update_data['status'] != old_status:
        activity_log = TaskActivityLog(
            task_id=task.id,
            event_type="STATUS_CHANGED",
            payload_json=json.dumps({
                "old_status": str(old_status),
                "new_status": str(task.status)
            }),
            created_by=current_user.id
        )
        db.add(activity_log)

    # Log si se asignó
    if 'assignee_user_id' in update_data:
        activity_log = TaskActivityLog(
            task_id=task.id,
            event_type="ASSIGNED",
            payload_json=json.dumps({
                "assignee_user_id": task.assignee_user_id
            }),
            created_by=current_user.id
        )
        db.add(activity_log)
    
    await db.commit()
    await db.refresh(task)
    
    return task


# =======================
# EVIDENCE ENDPOINTS
# =======================

@router.post("/tasks/{task_id}/evidences", response_model=EvidenceResponse, status_code=201)
async def upload_evidence(
    task_id: int,
    file: UploadFile = File(...),
    evidence_type: str = "OTRO",
    comment: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Subir evidencia a una tarea"""
    
    # Verificar tarea
    result = await db.execute(
        select(ProjectTask).join(
            Project, ProjectTask.project_id == Project.id
        ).where(
            and_(
                ProjectTask.id == task_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Subir archivo a storage
    try:
        file_content = await file.read()
        
        # Sanitizar nombre de archivo (reemplazar espacios y caracteres especiales)
        import re
        from urllib.parse import quote
        safe_filename = re.sub(r'[^\w\.-]', '_', file.filename)
        storage_key = f"projects/{task.project_id}/tasks/{task_id}/{safe_filename}"
        
        minio_client.upload_file(
            bucket_name="evidencias",
            object_name=storage_key,
            data=file_content,
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Generar URL firmada
        file_url = minio_client.get_presigned_url(
            bucket_name="evidencias",
            object_name=storage_key
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )
    
    # Crear registro de evidencia
    db_evidence = TaskEvidence(
        task_id=task_id,
        storage_key=storage_key,
        file_url=file_url,
        filename=file.filename,
        mime_type=file.content_type,
        size_bytes=len(file_content),
        evidence_type=evidence_type,
        comment=comment,
        uploaded_by=current_user.id
    )
    db.add(db_evidence)
    
    # Log de actividad
    activity_log = TaskActivityLog(
        task_id=task_id,
        event_type="EVIDENCE_ADDED",
        payload_json=json.dumps({
            "filename": file.filename,
            "evidence_type": evidence_type
        }),
        created_by=current_user.id
    )
    db.add(activity_log)
    
    await db.commit()
    await db.refresh(db_evidence)
    
    # Obtener nombre del uploader
    uploader_result = await db.execute(
        select(User.full_name).where(User.id == current_user.id)
    )
    uploader_name = uploader_result.scalar_one_or_none()
    
    # Construir response con uploader_name
    return EvidenceResponse(
        id=db_evidence.id,
        task_id=db_evidence.task_id,
        storage_key=db_evidence.storage_key,
        file_url=db_evidence.file_url,
        filename=db_evidence.filename,
        mime_type=db_evidence.mime_type,
        size_bytes=db_evidence.size_bytes,
        evidence_type=db_evidence.evidence_type,
        comment=db_evidence.comment,
        uploaded_by=db_evidence.uploaded_by,
        uploader_name=uploader_name,
        uploaded_at=db_evidence.uploaded_at
    )


@router.get("/tasks/{task_id}/evidences", response_model=List[EvidenceResponse])
async def list_evidences(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Listar evidencias de una tarea"""
    
    # Verificar tarea
    result = await db.execute(
        select(ProjectTask).join(
            Project, ProjectTask.project_id == Project.id
        ).where(
            and_(
                ProjectTask.id == task_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Obtener evidencias con nombre del uploader
    result = await db.execute(
        select(TaskEvidence, User.full_name.label('uploader_name'))
        .join(User, TaskEvidence.uploaded_by == User.id, isouter=True)
        .where(TaskEvidence.task_id == task_id)
        .order_by(TaskEvidence.uploaded_at.desc())
    )
    rows = result.all()

    response = []
    for evidence, uploader_name in rows:
        try:
            url = minio_client.get_presigned_url("evidencias", evidence.storage_key)
        except Exception:
            url = evidence.file_url
        response.append({
            "id": evidence.id,
            "task_id": evidence.task_id,
            "filename": evidence.filename,
            "storage_key": evidence.storage_key,
            "file_url": url,
            "mime_type": evidence.mime_type,
            "size_bytes": evidence.size_bytes,
            "evidence_type": evidence.evidence_type,
            "comment": evidence.comment,
            "uploaded_by": evidence.uploaded_by,
            "uploader_name": uploader_name,
            "uploaded_at": evidence.uploaded_at,
        })

    return response


@router.delete("/evidences/{evidence_id}", status_code=204)
async def delete_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar evidencia (con permisos)"""
    
    # Obtener evidencia
    result = await db.execute(
        select(TaskEvidence).join(
            ProjectTask, TaskEvidence.task_id == ProjectTask.id
        ).join(
            Project, ProjectTask.project_id == Project.id
        ).where(
            and_(
                TaskEvidence.id == evidence_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    evidence = result.scalars().first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    # Verificar permisos (solo el que subió o admin puede borrar)
    if evidence.uploaded_by != current_user.id and not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this evidence")
    
    # Eliminar de storage
    try:
        await minio_client.delete_file(
            bucket="evidences",
            key=evidence.storage_key
        )
    except:
        pass  # Si falla, continuar
    
    # Log de actividad
    activity_log = TaskActivityLog(
        task_id=evidence.task_id,
        event_type="EVIDENCE_DELETED",
        payload_json=json.dumps({
            "filename": evidence.filename
        }),
        created_by=current_user.id
    )
    db.add(activity_log)
    
    # Eliminar registro
    await db.delete(evidence)
    await db.commit()
    
    return None


# =======================
# COMMENT & ACTIVITY ENDPOINTS
# =======================

@router.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    task_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Agregar comentario a una tarea"""
    
    # Verificar tarea
    result = await db.execute(
        select(ProjectTask).join(
            Project, ProjectTask.project_id == Project.id
        ).where(
            and_(
                ProjectTask.id == task_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Crear comentario
    db_comment = TaskComment(
        task_id=task_id,
        created_by=current_user.id,
        comment=comment_data.comment
    )
    db.add(db_comment)
    
    # Log de actividad
    activity_log = TaskActivityLog(
        task_id=task_id,
        event_type="COMMENT_ADDED",
        payload_json=json.dumps({"comment_preview": comment_data.comment[:100]}),
        created_by=current_user.id
    )
    db.add(activity_log)
    
    await db.commit()
    await db.refresh(db_comment)
    
    return db_comment


@router.get("/tasks/{task_id}/comments", response_model=List[CommentResponse])
async def list_comments(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Listar comentarios de una tarea"""
    
    # Verificar tarea
    result = await db.execute(
        select(ProjectTask).join(
            Project, ProjectTask.project_id == Project.id
        ).where(
            and_(
                ProjectTask.id == task_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Obtener comentarios
    result = await db.execute(
        select(TaskComment).where(
            TaskComment.task_id == task_id
        ).order_by(TaskComment.created_at.desc())
    )
    return result.scalars().all()


@router.get("/tasks/{task_id}/activity", response_model=List[ActivityLogResponse])
async def get_task_activity(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener timeline de actividad de una tarea"""
    
    # Verificar tarea
    result = await db.execute(
        select(ProjectTask).join(
            Project, ProjectTask.project_id == Project.id
        ).where(
            and_(
                ProjectTask.id == task_id,
                Project.tenant_id == current_user.tenant_id
            )
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Obtener actividad
    result = await db.execute(
        select(TaskActivityLog).where(
            TaskActivityLog.task_id == task_id
        ).order_by(TaskActivityLog.created_at.desc())
    )
    return result.scalars().all()
