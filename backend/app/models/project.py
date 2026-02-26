"""Modelos para Proyectos y Tareas"""
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, ForeignKey, DateTime, Text, Float, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class ProjectType(str, enum.Enum):
    """Tipos de proyecto"""
    AUDITORIA = "AUDITORIA"
    CORRECTIVO = "CORRECTIVO"
    MANTENIMIENTO = "MANTENIMIENTO"
    REVISION_RUTINA = "REVISION_RUTINA"
    TC = "TC"


class ProjectStatus(str, enum.Enum):
    """Estados de proyecto"""
    ABIERTO = "ABIERTO"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADO = "COMPLETADO"
    CERRADO = "CERRADO"


class TaskType(str, enum.Enum):
    """Tipos de tarea"""
    OBLIGATION = "OBLIGATION"  # Basada en catálogo de obligaciones
    CUSTOM = "CUSTOM"  # Tarea adicional custom


class TaskStatus(str, enum.Enum):
    """Estados de tarea"""
    NO_INICIADO = "NO_INICIADO"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADO = "COMPLETADO"
    CERRADO = "CERRADO"


class Priority(str, enum.Enum):
    """Prioridad"""
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class EvidenceType(str, enum.Enum):
    """Tipos de evidencia"""
    MEDICION = "MEDICION"
    FOTO = "FOTO"
    INFORME = "INFORME"
    BITACORA = "BITACORA"
    DICTAMEN = "DICTAMEN"
    MANUAL = "MANUAL"
    OTRO = "OTRO"


class Project(Base):
    """Proyecto de trabajo vinculado a una empresa"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    
    # Metadata del proyecto
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(SQLEnum(ProjectType), nullable=False, index=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.ABIERTO, nullable=False, index=True)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIA, nullable=True)
    
    # Fechas
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Auditoría
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tenant = relationship("Tenant", back_populates="projects")
    company = relationship("Company", back_populates="projects")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")


class ProjectTask(Base):
    """Tarea dentro de un proyecto"""
    __tablename__ = "project_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Tipo y referencia
    task_type = Column(SQLEnum(TaskType), nullable=False, default=TaskType.OBLIGATION)
    requirement_id = Column(Integer, ForeignKey("compliance_requirements.id"), nullable=True)  # Solo si OBLIGATION
    
    # Contenido
    code = Column(String(50), nullable=True)  # Ej: "2.8.1" (copiado del requirement o custom)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    
    # Estado y asignación
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.NO_INICIADO, nullable=False, index=True)
    assignee_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    
    # Progreso y notas
    progress_percentage = Column(Integer, default=0, nullable=False)  # 0-100
    sort_order = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Auditoría
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    project = relationship("Project", back_populates="tasks")
    requirement = relationship("ComplianceRequirement")
    assignee = relationship("User", foreign_keys=[assignee_user_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    evidences = relationship("TaskEvidence", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    activity_logs = relationship("TaskActivityLog", back_populates="task", cascade="all, delete-orphan")


class TaskEvidence(Base):
    """Evidencia/documento adjunto a una tarea"""
    __tablename__ = "task_evidences"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False, index=True)
    
    # Archivo
    storage_key = Column(String(500), nullable=False)  # Key en MinIO/S3
    file_url = Column(String(1000), nullable=True)  # URL firmada temporal
    filename = Column(String(300), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    
    # Metadata
    evidence_type = Column(SQLEnum(EvidenceType), default=EvidenceType.OTRO, nullable=False)
    comment = Column(Text, nullable=True)
    
    # Auditoría
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    task = relationship("ProjectTask", back_populates="evidences")
    uploader = relationship("User")


class TaskComment(Base):
    """Comentario en una tarea"""
    __tablename__ = "task_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False, index=True)
    
    comment = Column(Text, nullable=False)
    
    # Auditoría
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    task = relationship("ProjectTask", back_populates="comments")
    creator = relationship("User")


class TaskActivityLog(Base):
    """Log de actividad/cambios en una tarea"""
    __tablename__ = "task_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False, index=True)
    
    # Tipo de evento
    event_type = Column(String(50), nullable=False)  # STATUS_CHANGED, ASSIGNED, EVIDENCE_ADDED, etc.
    payload_json = Column(Text, nullable=True)  # JSON con detalles del cambio
    
    # Auditoría
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    task = relationship("ProjectTask", back_populates="activity_logs")
    creator = relationship("User")
