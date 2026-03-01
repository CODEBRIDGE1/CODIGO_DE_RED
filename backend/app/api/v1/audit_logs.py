"""
Audit Logs – Tenant endpoint
Consulta de bitácora filtrada por tenant del usuario autenticado.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime, date

from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.dependencies import get_current_active_user
from app.api.v1.admin.audit_logs import AuditLogItem, AuditLogListResponse

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_my_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    module_key: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Bitácora filtrada por el tenant del usuario autenticado.
    Si es superadmin, ve todo (misma vista que el endpoint admin).
    """
    filters = []
    if not current_user.is_superadmin:
        filters.append(AuditLog.tenant_id == current_user.tenant_id)

    if module_key:
        filters.append(AuditLog.module_key == module_key)
    if action:
        filters.append(AuditLog.action == action)
    if date_from:
        filters.append(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        filters.append(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))

    where = and_(*filters) if filters else True

    count_result = await db.execute(select(func.count()).select_from(AuditLog).where(where))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(AuditLog)
        .where(where)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    user_ids = {log.user_id for log in logs if log.user_id}
    users_map: dict[int, str] = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.email).where(User.id.in_(user_ids))
        )
        users_map = {row.id: row.email for row in users_result}

    items = [
        AuditLogItem(
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
        )
        for log in logs
    ]

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.get("/modules", response_model=List[str])
async def list_my_modules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filters = [] if current_user.is_superadmin else [AuditLog.tenant_id == current_user.tenant_id]
    where = and_(*filters) if filters else True
    result = await db.execute(
        select(AuditLog.module_key).where(where).distinct().order_by(AuditLog.module_key)
    )
    return [row[0] for row in result if row[0]]


@router.get("/actions", response_model=List[str])
async def list_my_actions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filters = [] if current_user.is_superadmin else [AuditLog.tenant_id == current_user.tenant_id]
    where = and_(*filters) if filters else True
    result = await db.execute(
        select(AuditLog.action).where(where).distinct().order_by(AuditLog.action)
    )
    return [row[0] for row in result if row[0]]
