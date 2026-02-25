# CÓDIGO COMPLETO - PLATAFORMA CÓDIGO DE RED
## Archivos Restantes del Proyecto

Este documento contiene TODOS los archivos restantes necesarios para completar el proyecto.
Copiar cada sección en el archivo correspondiente.

---

## BACKEND - MODELOS SQLAlchemy

### backend/app/models/__init__.py
```python
# Empty init file
```

### backend/app/models/license.py
```python
"""License Model - Licencias por tenant"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class License(Base):
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), unique=True, nullable=False, index=True)
    max_users = Column(Integer, default=10, nullable=False)
    max_storage_gb = Column(Integer, default=50, nullable=False)
    current_storage_gb = Column(Float, default=0.0, nullable=False)
    enabled_modules = Column(JSON, nullable=False)  # ["companies", "obligations", ...]
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="license")
```

### backend/app/models/user.py
```python
"""User Model"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
```

### backend/app/models/role.py
```python
"""Role Models"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
```

### backend/app/models/permission.py
```python
"""Permission Model"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(String(500))
    
    module = relationship("Module", back_populates="permissions")
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
```

### backend/app/models/module.py
```python
"""Module Model"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class Module(Base):
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    icon = Column(String(50))
    shortcut_key = Column(String(1))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    permissions = relationship("Permission", back_populates="module", cascade="all, delete-orphan")
```

### backend/app/models/audit_log.py
```python
"""Audit Log Model"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    module_key = Column(String(50), index=True)
    action = Column(String(50), index=True)
    entity_type = Column(String(50))
    entity_id = Column(Integer, nullable=True)
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    request_id = Column(String(50), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
```

### backend/app/models/company.py
```python
"""Company Model"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    rfc = Column(String(20))
    region = Column(String(50))
    installed_capacity_kw = Column(Float)
    voltage_level = Column(String(50))
    has_generation = Column(Boolean, default=False)
    address = Column(Text)
    contact_name = Column(String(200))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    status = Column(String(50), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="companies")
    obligations = relationship("CompanyObligation", back_populates="company", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")
    evidences = relationship("Evidence", back_populates="company", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="company", cascade="all, delete-orphan")
```

### backend/app/models/obligation.py
```python
"""Obligation Models"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Obligation(Base):
    __tablename__ = "obligations"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    sub_category = Column(String(100))
    normative_reference = Column(String(200))
    frequency = Column(String(50))
    applies_to = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company_obligations = relationship("CompanyObligation", back_populates="obligation")

class CompanyObligation(Base):
    __tablename__ = "company_obligations"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    obligation_id = Column(Integer, ForeignKey("obligations.id"), nullable=False, index=True)
    status = Column(String(50), default="pending_review", index=True)
    notes = Column(Text)
    responsible_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    last_reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("Company", back_populates="obligations")
    obligation = relationship("Obligation", back_populates="company_obligations")
```

### backend/app/models/project.py
```python
"""Project and Task Models"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    obligation_id = Column(Integer, ForeignKey("obligations.id"), nullable=True)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="planning", index=True)
    priority = Column(String(50), default="medium")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    progress_percent = Column(Integer, default=0)
    budget = Column(Numeric(15, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="projects")
    company = relationship("Company", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="pending", index=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="tasks")
```

### backend/app/models/evidence.py
```python
"""Evidence Model"""
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Evidence(Base):
    __tablename__ = "evidences"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    obligation_id = Column(Integer, ForeignKey("obligations.id"), nullable=True)
    file_key = Column(String(500), nullable=False, unique=True, index=True)
    filename = Column(String(300), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(BigInteger, nullable=False)
    description = Column(Text)
    tags = Column(JSON, default=list)
    checksum = Column(String(64))
    version = Column(Integer, default=1)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="evidences")
    company = relationship("Company", back_populates="evidences")
```

### backend/app/models/quote.py
```python
"""Quote Models"""
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    quote_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="draft", index=True)
    subtotal = Column(Numeric(15, 2), default=0)
    tax_percent = Column(Numeric(5, 2), default=16)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)
    currency = Column(String(10), default="MXN")
    valid_until = Column(Date, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="quotes")
    company = relationship("Company", back_populates="quotes")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")

class QuoteItem(Base):
    __tablename__ = "quote_items"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    quote = relationship("Quote", back_populates="items")
```

---

## BACKEND - SCHEMAS (Pydantic)

### backend/app/schemas/__init__.py
```python
# Empty init
```

### backend/app/schemas/auth.py
```python
"""Auth Schemas"""
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshRequest(BaseModel):
    refresh_token: str
```

### backend/app/schemas/tenant.py
```python
"""Tenant Schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TenantCreate(BaseModel):
    name: str
    subdomain: str

class TenantResponse(BaseModel):
    id: int
    name: str
    subdomain: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### backend/app/schemas/company.py
```python
"""Company Schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CompanyCreate(BaseModel):
    name: str
    rfc: Optional[str] = None
    region: Optional[str] = None
    installed_capacity_kw: Optional[float] = None
    voltage_level: Optional[str] = None
    has_generation: bool = False
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

class CompanyResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    rfc: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

---

## BACKEND - API ENDPOINTS

### backend/app/api/v1/dependencies.py
```python
"""API Dependencies"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.tenant import get_current_tenant_id
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user
```

### backend/app/api/v1/router.py
```python
"""API V1 Router"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, companies

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
# Include other routers...
```

### backend/app/api/v1/endpoints/auth.py
```python
"""Auth Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.config import settings
from app.core.audit import log_auth_event, get_audit_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    audit_ctx = get_audit_context(request)
    
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        await log_auth_event(
            db=db, action="failed_login", user_id=None,
            email=credentials.email, success=False,
            ip_address=audit_ctx["ip_address"],
            user_agent=audit_ctx["user_agent"],
            request_id=audit_ctx["request_id"],
            reason="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    
    await log_auth_event(
        db=db, action="login", user_id=user.id,
        email=user.email, success=True,
        ip_address=audit_ctx["ip_address"],
        user_agent=audit_ctx["user_agent"],
        request_id=audit_ctx["request_id"]
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
```

### backend/app/api/v1/endpoints/companies.py
```python
"""Companies Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.rbac import require_permission
from app.core.tenant import get_current_tenant_id, apply_tenant_filter
from app.core.audit import log_entity_change
from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyResponse
from app.api.v1.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "read"))
):
    tenant_id = get_current_tenant_id()
    result = await db.execute(
        apply_tenant_filter(select(Company), Company).where(Company.tenant_id == tenant_id)
    )
    companies = result.scalars().all()
    return companies

@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("companies", "create"))
):
    tenant_id = get_current_tenant_id()
    
    company = Company(**company_data.model_dump(), tenant_id=tenant_id)
    db.add(company)
    await db.flush()
    
    await log_entity_change(
        db=db, request=request, user_id=current_user.id,
        module_key="companies", action="create",
        entity_type="company", entity_id=company.id,
        after={"name": company.name, "rfc": company.rfc}
    )
    
    await db.commit()
    await db.refresh(company)
    return company
```

---

## BACKEND - Celery Workers

### backend/app/workers/__init__.py
```python
# Empty
```

### backend/app/workers/celery_app.py
```python
"""Celery App Configuration"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "codigo_red_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
)

# Periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "check-expiring-obligations": {
        "task": "app.workers.tasks.check_expiring_obligations",
        "schedule": crontab(hour=8, minute=0),  # Daily at 8 AM
    },
}
```

### backend/app/workers/tasks.py
```python
"""Celery Tasks"""
from celery import Task
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def recalculate_obligations_matrix(self, company_id: int):
    logger.info(f"Recalculating obligations matrix for company {company_id}")
    # TODO: Implement logic
    return {"company_id": company_id, "status": "completed"}

@celery_app.task
def generate_compliance_report_pdf(company_id: int, user_id: int):
    logger.info(f"Generating PDF report for company {company_id}")
    # TODO: Implement PDF generation
    return {"company_id": company_id, "report_url": "minio://..."}

@celery_app.task
def check_expiring_obligations():
    logger.info("Checking for expiring obligations...")
    # TODO: Implement expiration check and notifications
    return {"checked": True, "notifications_sent": 0}
```

---

## BACKEND - Alembic Migration

### backend/alembic/env.py
```python
"""Alembic Environment Configuration"""
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio

from app.core.config import settings
from app.db.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### backend/alembic/versions/0001_initial.py
```python
"""initial migration

Revision ID: 0001
Revises: 
Create Date: 2024-02-22 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('subdomain', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'SUSPENDED', 'GRACE_PERIOD', 'DELETED', name='tenantstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subdomain')
    )
    op.create_index('ix_tenants_name', 'tenants', ['name'])
    op.create_index('ix_tenants_subdomain', 'tenants', ['subdomain'])
    
    # Create licenses table
    op.create_table('licenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('max_users', sa.Integer(), nullable=False),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False),
        sa.Column('current_storage_gb', sa.Float(), nullable=False),
        sa.Column('enabled_modules', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )
    
    # Create modules table
    op.create_table('modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('shortcut_key', sa.String(length=1), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superadmin', sa.Boolean(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create role_permissions table
    op.create_table('role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('module_key', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('before_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('after_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('rfc', sa.String(length=20), nullable=True),
        sa.Column('region', sa.String(length=50), nullable=True),
        sa.Column('installed_capacity_kw', sa.Float(), nullable=True),
        sa.Column('voltage_level', sa.String(length=50), nullable=True),
        sa.Column('has_generation', sa.Boolean(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('contact_name', sa.String(length=200), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create other tables (obligations, projects, evidences, quotes)...
    # Omitted for brevity, follow same pattern

def downgrade() -> None:
    op.drop_table('companies')
    op.drop_table('audit_logs')
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
    op.drop_table('modules')
    op.drop_table('licenses')
    op.drop_table('tenants')
```

---

## BACKEND - Seed Script

### backend/scripts/seed.py
```python
#!/usr/bin/env python3
"""
Seed database with initial data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.tenant import Tenant, TenantStatus
from app.models.license import License
from app.models.user import User
from app.models.role import Role, UserRole, RolePermission
from app.models.module import Module
from app.models.permission import Permission

async def seed_database():
    print("🌱 Seeding database...")
    
    async with AsyncSessionLocal() as db:
        # 1. Create Modules
        modules_data = [
            {"key": "dashboard", "name": "Dashboard", "icon": "home", "shortcut_key": "D", "sort_order": 1},
            {"key": "companies", "name": "Empresas", "icon": "building", "shortcut_key": "E", "sort_order": 2},
            {"key": "obligations", "name": "Obligaciones", "icon": "checklist", "shortcut_key": "O", "sort_order": 3},
            {"key": "projects", "name": "Proyectos", "icon": "folder", "shortcut_key": "P", "sort_order": 4},
            {"key": "evidences", "name": "Evidencias", "icon": "file", "shortcut_key": "V", "sort_order": 5},
            {"key": "quotes", "name": "Cotizaciones", "icon": "document", "shortcut_key": "C", "sort_order": 6},
            {"key": "users", "name": "Usuarios", "icon": "users", "shortcut_key": "U", "sort_order": 7},
            {"key": "audit", "name": "Bitácora", "icon": "clock", "shortcut_key": "B", "sort_order": 8},
            {"key": "admin_tenants", "name": "Admin Tenants", "icon": "shield", "shortcut_key": "T", "sort_order": 9},
        ]
        
        modules = []
        for mod_data in modules_data:
            module = Module(**mod_data, is_active=True)
            db.add(module)
            modules.append(module)
        await db.flush()
        print(f"✓ Created {len(modules)} modules")
        
        # 2. Create Permissions
        actions = ["read", "create", "update", "delete", "export", "manage_users", "view_audit"]
        permissions = []
        for module in modules:
            for action in actions:
                if module.key == "dashboard" and action not in ["read"]:
                    continue
                perm = Permission(module_id=module.id, action=action, description=f"{action} {module.name}")
                db.add(perm)
                permissions.append(perm)
        await db.flush()
        print(f"✓ Created {len(permissions)} permissions")
        
        # 3. Create Superadmin User
        superadmin = User(
            email="superadmin@codebridge.com",
            hashed_password=hash_password("SuperAdmin123!"),
            full_name="Super Admin",
            is_superadmin=True,
            is_active=True
        )
        db.add(superadmin)
        await db.flush()
        print(f"✓ Created superadmin user: {superadmin.email}")
        
        # 4. Create Demo Tenant
        demo_tenant = Tenant(
            name="Tenant Demo",
            subdomain="tenant-demo",
            status=TenantStatus.ACTIVE
        )
        db.add(demo_tenant)
        await db.flush()
        
        demo_license = License(
            tenant_id=demo_tenant.id,
            max_users=50,
            max_storage_gb=100,
            enabled_modules=["companies", "obligations", "projects", "evidences", "quotes", "users", "audit"],
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db.add(demo_license)
        print(f"✓ Created demo tenant: {demo_tenant.subdomain}")
        
        # 5. Create Admin Role for Tenant
        admin_role = Role(
            tenant_id=demo_tenant.id,
            name="Admin",
            description="Administrador con todos los permisos",
            is_system=True
        )
        db.add(admin_role)
        await db.flush()
        
        # Assign all permissions to admin role
        for perm in permissions:
            if perm.module.key != "admin_tenants":  # Skip global admin module
                role_perm = RolePermission(role_id=admin_role.id, permission_id=perm.id)
                db.add(role_perm)
        
        # 6. Create Admin User for Tenant
        admin_user = User(
            tenant_id=demo_tenant.id,
            email="admin@tenant-demo.com",
            hashed_password=hash_password("Admin123!"),
            full_name="Admin Demo",
            is_active=True,
            is_superadmin=False
        )
        db.add(admin_user)
        await db.flush()
        
        user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
        db.add(user_role)
        print(f"✓ Created admin user for tenant: {admin_user.email}")
        
        # 7. Create Operador Role
        operador_role = Role(
            tenant_id=demo_tenant.id,
            name="Operador",
            description="Usuario operativo con permisos limitados",
            is_system=True
        )
        db.add(operador_role)
        await db.flush()
        
        # Assign limited permissions
        limited_perms = [p for p in permissions if p.action in ["read", "create", "update", "export"] 
                        and p.module.key in ["companies", "obligations", "projects", "evidences"]]
        for perm in limited_perms:
            role_perm = RolePermission(role_id=operador_role.id, permission_id=perm.id)
            db.add(role_perm)
        
        # 8. Create Operador User
        operador_user = User(
            tenant_id=demo_tenant.id,
            email="operador@tenant-demo.com",
            hashed_password=hash_password("Operador123!"),
            full_name="Operador Demo",
            is_active=True,
            is_superadmin=False
        )
        db.add(operador_user)
        await db.flush()
        
        user_role = UserRole(user_id=operador_user.id, role_id=operador_role.id)
        db.add(user_role)
        print(f"✓ Created operador user: {operador_user.email}")
        
        # Commit all
        await db.commit()
        
        print("\n" + "="*60)
        print("✓ Database seeded successfully!")
        print("="*60)
        print("\nUSERS CREATED:")
        print(f"  Superadmin: superadmin@codebridge.com / SuperAdmin123!")
        print(f"  Tenant Admin: admin@tenant-demo.com / Admin123!")
        print(f"  Tenant Operador: operador@tenant-demo.com / Operador123!")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(seed_database())
```

---

## FRONTEND - Configuración

### frontend/Dockerfile
```dockerfile
FROM node:20-alpine as development

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Production stage
FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine as production

COPY --from=build /app/dist /usr/share/nginx/html
COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### frontend/package.json
```json
{
  "name": "codigo-red-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-check --tsconfig ./tsconfig.json"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "@tsconfig/svelte": "^5.0.2",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "svelte": "^5.0.0",
    "svelte-check": "^3.6.2",
    "tailwindcss": "^3.4.0",
    "tslib": "^2.6.2",
    "typescript": "^5.3.3",
    "vite": "^5.0.8"
  },
  "type": "module",
  "dependencies": {
    "@sveltejs/kit": "^2.0.0"
  }
}
```

### frontend/vite.config.ts
```typescript
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true
      }
    }
  }
});
```

### frontend/tailwind.config.cjs
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

### frontend/tsconfig.json
```json
{
  "extends": "@tsconfig/svelte/tsconfig.json",
  "compilerOptions": {
    "target": "ESNext",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "resolveJsonModule": true,
    "allowJs": true,
    "checkJs": true,
    "isolatedModules": true,
    "moduleDetection": "force"
  },
  "include": ["src/**/*.d.ts", "src/**/*.ts", "src/**/*.js", "src/**/*.svelte"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## FRONTEND - Core Libraries

### frontend/src/main.ts
```typescript
import './app.css';
import App from './App.svelte';

const app = new App({
  target: document.getElementById('app')!,
});

export default app;
```

### frontend/src/app.css
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --primary: #3b82f6;
  --secondary: #64748b;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
}

body {
  @apply bg-gray-50 text-gray-900;
}
```

### frontend/src/lib/api/client.ts
```typescript
/**
 * API Client con manejo automático de refresh tokens
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

let accessToken: string | null = null;
let refreshToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function getAccessToken(): string | null {
  if (!accessToken) {
    accessToken = localStorage.getItem('access_token');
  }
  return accessToken;
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh })
    });

    if (response.ok) {
      const data = await response.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    }
  } catch (error) {
    console.error('Failed to refresh token:', error);
  }

  clearTokens();
  return false;
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();
  const tenantId = localStorage.getItem('tenant_id');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (tenantId) {
    headers['X-Tenant-ID'] = tenantId;
  }

  let response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  // Si 401, intentar refresh
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // Retry request con nuevo token
      headers['Authorization'] = `Bearer ${getAccessToken()}`;
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
      });
    } else {
      // Redirect a login
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  get: <T = any>(endpoint: string) => apiRequest<T>(endpoint, { method: 'GET' }),
  post: <T = any>(endpoint: string, data: any) => apiRequest<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T = any>(endpoint: string, data: any) => apiRequest<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  delete: <T = any>(endpoint: string) => apiRequest<T>(endpoint, { method: 'DELETE' }),
};
```

### frontend/src/lib/stores/auth.ts
```typescript
/**
 * Auth Store - Svelte 5 Runes
 */
import { writable } from 'svelte/store';
import { setTokens, clearTokens, api } from '../api/client';

interface User {
  id: number;
  email: string;
  full_name: string;
  is_superadmin: boolean;
}

export const user = writable<User | null>(null);
export const isAuthenticated = writable<boolean>(false);

export async function login(email: string, password: string): Promise<void> {
  const data = await api.post('/api/v1/auth/login', { email, password });
  
  setTokens(data.access_token, data.refresh_token);
  user.set(data.user);
  isAuthenticated.set(true);
  
  if (data.user.tenant_id) {
    localStorage.setItem('tenant_id', data.user.tenant_id.toString());
  }
}

export function logout(): void {
  clearTokens();
  user.set(null);
  isAuthenticated.set(false);
  localStorage.removeItem('tenant_id');
  window.location.href = '/login';
}

export async function checkAuth(): Promise<void> {
  try {
    const data = await api.get('/api/v1/auth/me');
    user.set(data);
    isAuthenticated.set(true);
  } catch {
    logout();
  }
}
```

### frontend/src/lib/stores/permissions.ts
```typescript
/**
 * Permissions Store
 */
import { writable } from 'svelte/store';

export const permissions = writable<Record<string, string[]>>({});

export function hasPermission(module: string, action: string): boolean {
  let perms: Record<string, string[]> = {};
  permissions.subscribe(p => perms = p)();
  
  return perms[module]?.includes(action) || false;
}
```

### frontend/src/lib/shortcuts/registry.ts
```typescript
/**
 * Keyboard Shortcuts Registry
 */

type ShortcutHandler = () => void;

const shortcuts: Map<string, ShortcutHandler> = new Map();

export function registerShortcut(key: string, handler: ShortcutHandler) {
  shortcuts.set(key.toLowerCase(), handler);
}

export function unregisterShortcut(key: string) {
  shortcuts.delete(key.toLowerCase());
}

export function initializeShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Global shortcuts (ALT + key)
    if (e.altKey && !e.ctrlKey && !e.shiftKey) {
      const key = e.key.toLowerCase();
      const handler = shortcuts.get(`alt+${key}`);
      if (handler) {
        e.preventDefault();
        handler();
      }
    }
    
    // Module shortcuts (single key, no input focus)
    if (!e.altKey && !e.ctrlKey && !e.metaKey) {
      const target = e.target as HTMLElement;
      if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
        const key = e.key.toLowerCase();
        const handler = shortcuts.get(key);
        if (handler) {
          e.preventDefault();
          handler();
        }
      }
    }
  });
}
```

---

## COMANDOS PARA EJECUTAR EL PROYECTO

```bash
# 1. Clonar variables de entorno
cp .env.example .env

# 2. Levantar infraestructura
docker-compose up -d

# 3. Esperar a que servicios estén listos (30 segundos aprox)
sleep 30

# 4. Ejecutar migraciones
docker-compose exec api alembic upgrade head

# 5. Ejecutar seed de datos iniciales
docker-compose exec api python scripts/seed.py

# 6. Ver logs
docker-compose logs -f api

# 7. Acceder a la aplicación
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
# MinIO Console: http://localhost:9001 (minioadmin / minioadmin_secret_change_me)

# 8. Login de prueba
# Superadmin: superadmin@codebridge.com / SuperAdmin123!
# Tenant Admin: admin@tenant-demo.com / Admin123!
# Tenant Operador: operador@tenant-demo.com / Operador123!
```

---

## PRÓXIMOS PASOS PARA COMPLETAR

1. **Completar endpoints faltantes** (obligations, projects, evidences, quotes, users_roles, audit, tenants_admin)
2. **Completar schemas Pydantic** para cada endpoint
3. **Completar modelos faltantes** en migrations (obligations, projects, evidences, quotes completos)
4. **Frontend**: crear componentes Svelte (Sidebar.svelte, Modal.svelte, Toast.svelte)
5. **Frontend**: crear rutas completas (+page.svelte para cada módulo)
6. **Frontend**: implementar shortcuts globales
7. **Integración MinIO**: implementar presigned URLs completas
8. **Tests**: agregar pytest para backend y Playwright para frontend
9. **CI/CD**: agregar GitHub Actions
10. **Observabilidad**: agregar Prometheus + Grafana

---

## NOTAS IMPORTANTES

- **Este código es un MVP funcional** pero requiere expansión en endpoints y vistas
- **Seguridad**: cambiar todos los secrets en producción (.env)
- **MinIO**: crear bucket "evidences" manualmente la primera vez o con script init
- **Alembic**: la migración 0001 es parcial, agregar tablas faltantes
- **Frontend**: implementar manejo de errores y loading states
- **RBAC**: está implementado en core pero falta aplicar en TODOS los endpoints
- **Audit**: middleware funciona pero falta integrar en todos los endpoints

---

FIN DEL DOCUMENTO CONSOLIDADO
