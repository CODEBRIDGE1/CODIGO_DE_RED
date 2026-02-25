"""
Project Models - Complete
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.base import Base


# ==================
# ENUMS
# ==================

class ProjectType(str, Enum):
    """Tipos de proyecto"""
    AUDITORIA = "AUDITORIA"
    MANTENIMIENTO = "MANTENIMIENTO"
    CORRECTIVO = "CORRECTIVO"
    REVISION_RUTINA = "REVISION_RUTINA"
    TC = "TC"


class Priority(str, Enum):
    """Prioridades"""
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class ProjectStatus(str, Enum):
    """Estados del proyecto"""
    ABIERTO = "ABIERTO"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADO = "COMPLETADO"
    CERRADO = "CERRADO"


class TaskStatus(str, Enum):
    """Estados de tarea"""
    NO_INICIADO = "NO_INICIADO"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADO = "COMPLETADO"
    CERRADO = "CERRADO"


class TaskType(str, Enum):
    """Tipos de tarea"""
    OBLIGATION = "OBLIGATION"  # Vinculada a obligación de compliance
    CUSTOM = "CUSTOM"  # Tarea personalizada


# ==================
# MODELS
# ==================

class Project(Base):
    """Proyecto vinculado a una empresa"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    project_type = Column(SQLEnum(ProjectType), nullable=False, index=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.ABIERTO, nullable=False, index=True)
    priority = Column(SQLEnum(Priority))
    
    start_date = Column(Date)
    due_date = Column(Date)
    completed_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="projects")
    company = relationship("Company", back_populates="projects")
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")


class ProjectTask(Base):
    """Tarea dentro de un proyecto"""
    __tablename__ = "project_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    task_type = Column(SQLEnum(TaskType), default=TaskType.CUSTOM, nullable=False)
    requirement_id = Column(Integer, ForeignKey("compliance_requirements.id"), nullable=True)
    
    code = Column(String(50))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.NO_INICIADO, nullable=False, index=True)
    
    assignee_user_id = Column(Integer, ForeignKey("users.id"))
    due_date = Column(Date)
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    sort_order = Column(Integer, default=0)
    notes = Column(Text)
    
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    requirement = relationship("ComplianceRequirement", foreign_keys=[requirement_id])
    assignee = relationship("User", foreign_keys=[assignee_user_id])
    evidences = relationship("TaskEvidence", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    activity_logs = relationship("TaskActivityLog", back_populates="task", cascade="all, delete-orphan")


class TaskEvidence(Base):
    """Evidencias adjuntas a una tarea"""
    __tablename__ = "task_evidences"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False, index=True)
    
    storage_key = Column(String(500), nullable=False)
    file_url = Column(String(1000))
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100))
    size_bytes = Column(Integer)
    
    evidence_type = Column(SQLEnum('MEDICION', 'FOTO', 'INFORME', 'BITACORA', 'DICTAMEN', 'MANUAL', 'OTRO', name='evidencetype'), nullable=False)
    comment = Column(Text)
    
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    task = relationship("ProjectTask", back_populates="evidences")
    uploader = relationship("User", foreign_keys=[uploaded_by])


class TaskComment(Base):
    """Comentarios en tareas"""
    __tablename__ = "task_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    task = relationship("ProjectTask", back_populates="comments")
    creator = relationship("User", foreign_keys=[created_by])


class TaskActivityLog(Base):
    """Log de actividad de tareas"""
    __tablename__ = "task_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False)
    payload_json = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    task = relationship("ProjectTask", back_populates="activity_logs")
    creator = relationship("User", foreign_keys=[created_by])

