"""
Pydantic schemas for Projects module
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.models.project import ProjectStatus, TaskStatus, TaskType


# ==================
# PROJECT SCHEMAS
# ==================

class ProjectCreate(BaseModel):
    """Schema para crear proyecto"""
    company_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_type: str = Field(..., max_length=50)
    priority: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    """Schema para actualizar proyecto"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    project_type: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    """Schema de respuesta de proyecto"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tenant_id: int
    company_id: int
    name: str
    description: Optional[str]
    project_type: str
    status: ProjectStatus
    priority: Optional[str]
    start_date: Optional[date]
    due_date: Optional[date]
    completed_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]


class ProjectListItem(BaseModel):
    """Schema para listado de proyectos"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_id: int
    company_name: str
    name: str
    project_type: str
    status: ProjectStatus
    start_date: Optional[date]
    due_date: Optional[date]
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: int = 0


class TaskSummary(BaseModel):
    """Resumen de tarea para el detalle del proyecto"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_type: TaskType
    code: Optional[str]
    title: str
    description: Optional[str]
    status: TaskStatus
    assignee_user_id: Optional[int]
    assignee_name: Optional[str] = None
    due_date: Optional[date]
    progress_percentage: int = 0
    evidence_count: int = 0


class ProjectDetail(BaseModel):
    """Schema detallado de proyecto con tareas"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tenant_id: int
    company_id: int
    company_name: str
    name: str
    description: Optional[str]
    project_type: str
    status: ProjectStatus
    priority: Optional[str]
    start_date: Optional[date]
    due_date: Optional[date]
    completed_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    tasks: List[TaskSummary] = []
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: int = 0


class TaskMetrics(BaseModel):
    """Métricas de tareas de un proyecto"""
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    not_started_tasks: int = 0
    closed_tasks: int = 0
    completion_percentage: float = 0.0
    total_evidences: int = 0


class ProjectMetrics(BaseModel):
    """Métricas agregadas de proyectos"""
    total_projects: int
    active_projects: int
    completed_projects: int
    delayed_projects: int


# ==================
# TASK SCHEMAS
# ==================

class TaskCreate(BaseModel):
    """Schema para crear tarea"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: TaskType = TaskType.CUSTOM
    requirement_id: Optional[int] = None
    assignee_user_id: Optional[int] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


class TaskUpdate(BaseModel):
    """Schema para actualizar tarea"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    assignee_user_id: Optional[int] = None
    due_date: Optional[date] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class TaskResponse(BaseModel):
    """Schema de respuesta de tarea"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    task_type: TaskType
    requirement_id: Optional[int]
    code: Optional[str]
    title: str
    description: Optional[str]
    status: TaskStatus
    assignee_user_id: Optional[int]
    assignee_name: Optional[str] = None
    due_date: Optional[date]
    progress_percentage: int = 0
    sort_order: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# ==================
# EVIDENCE SCHEMAS
# ==================

class EvidenceCreate(BaseModel):
    """Schema para crear evidencia"""
    evidence_type: str = Field(..., max_length=50)
    comment: Optional[str] = None


class EvidenceResponse(BaseModel):
    """Schema de respuesta de evidencia"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    storage_key: str
    file_url: Optional[str]
    filename: str
    mime_type: Optional[str]
    size_bytes: Optional[int]
    evidence_type: str
    comment: Optional[str]
    uploaded_by: int
    uploader_name: Optional[str]
    uploaded_at: datetime


# ==================
# COMMENT SCHEMAS
# ==================

class CommentCreate(BaseModel):
    """Schema para crear comentario"""
    comment: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    """Schema de respuesta de comentario"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    user_id: int
    user_name: Optional[str]
    comment: str
    created_at: datetime


# ==================
# ACTIVITY LOG SCHEMAS
# ==================

class ActivityLogResponse(BaseModel):
    """Schema de respuesta de log de actividad"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    user_id: int
    user_name: Optional[str]
    action: str
    details: Optional[dict]
    created_at: datetime
