"""
Admin – Audit Logs
Consulta de la bitácora de acciones del sistema (solo superadmin)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel

from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.dependencies import get_current_superadmin

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AuditLogItem(BaseModel):
    id: int
    tenant_id: Optional[int]
    user_id: Optional[int]
    user_email: Optional[str] = None
    module_key: Optional[str]
    action: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[int]
    ip_address: Optional[str]
    after_data: Optional[dict]
    before_data: Optional[dict]
    request_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: List[AuditLogItem]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    tenant_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    module_key: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    """
    Listar entradas de la bitácora con filtros.
    Solo accesible para superadmin.
    """
    filters = []
    if tenant_id is not None:
        filters.append(AuditLog.tenant_id == tenant_id)
    if user_id is not None:
        filters.append(AuditLog.user_id == user_id)
    if module_key:
        filters.append(AuditLog.module_key == module_key)
    if action:
        filters.append(AuditLog.action == action)
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type)
    if date_from:
        filters.append(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        filters.append(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))

    where = and_(*filters) if filters else True

    # Total
    count_result = await db.execute(select(func.count()).select_from(AuditLog).where(where))
    total = count_result.scalar_one()

    # Paginated items
    offset = (page - 1) * page_size
    result = await db.execute(
        select(AuditLog)
        .where(where)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    # Enrich with user emails
    user_ids = {log.user_id for log in logs if log.user_id}
    users_map: dict[int, str] = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.email).where(User.id.in_(user_ids))
        )
        users_map = {row.id: row.email for row in users_result}

    items = []
    for log in logs:
        items.append(AuditLogItem(
            id=log.id,
            tenant_id=log.tenant_id,
            user_id=log.user_id,
            user_email=users_map.get(log.user_id) if log.user_id else None,
            module_key=log.module_key,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            ip_address=log.ip_address,
            after_data=log.after_data,
            before_data=log.before_data,
            request_id=log.request_id,
            created_at=log.created_at,
        ))

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, -(-total // page_size)),  # ceiling division
    )


@router.get("/modules", response_model=List[str])
async def list_modules(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    """Lista de módulos distintos que han generado entradas."""
    result = await db.execute(
        select(AuditLog.module_key).distinct().order_by(AuditLog.module_key)
    )
    return [row[0] for row in result if row[0]]


@router.get("/actions", response_model=List[str])
async def list_actions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superadmin),
):
    """Lista de acciones distintas registradas."""
    result = await db.execute(
        select(AuditLog.action).distinct().order_by(AuditLog.action)
    )
    return [row[0] for row in result if row[0]]
