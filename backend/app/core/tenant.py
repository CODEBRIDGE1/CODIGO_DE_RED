"""
Tenant Context Management - Multi-tenancy Core
Middleware y utilities para tenant scoping
"""
from typing import Optional
from contextvars import ContextVar
from fastapi import Request, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Context variable para almacenar tenant_id actual
_tenant_context: ContextVar[Optional[int]] = ContextVar("tenant_id", default=None)


class TenantContext:
    """
    Contexto de tenant para requests
    Almacena tenant_id en context variable para acceso global
    """
    
    @staticmethod
    def set_tenant_id(tenant_id: int | None) -> None:
        """Set current tenant ID"""
        _tenant_context.set(tenant_id)
    
    @staticmethod
    def get_tenant_id() -> int | None:
        """Get current tenant ID"""
        return _tenant_context.get()
    
    @staticmethod
    def clear() -> None:
        """Clear tenant context"""
        _tenant_context.set(None)
    
    @staticmethod
    def is_set() -> bool:
        """Check if tenant is set"""
        return _tenant_context.get() is not None


async def extract_tenant_from_request(request: Request) -> Optional[str]:
    """
    Extraer tenant identifier del request
    Soporta múltiples estrategias:
    1. Header X-Tenant-ID
    2. Subdominio (ej: tenant-demo.codigo-red.com)
    3. Path parameter (opcional)
    
    Args:
        request: FastAPI Request
        
    Returns:
        Tenant identifier (subdomain o ID) o None
    """
    # Strategy 1: Header X-Tenant-ID (más común en APIs)
    tenant_header = request.headers.get("X-Tenant-ID")
    if tenant_header:
        return tenant_header
    
    # Strategy 2: Subdominio
    host = request.headers.get("host", "")
    if "." in host:
        subdomain = host.split(".")[0]
        # Evitar subdomains comunes de infra
        if subdomain not in ["www", "api", "admin", "localhost"]:
            return subdomain
    
    # Strategy 3: Path parameter (si usamos /api/v1/tenants/{tenant_id}/...)
    # path_params = request.path_params
    # if "tenant_id" in path_params:
    #     return path_params["tenant_id"]
    
    return None


async def resolve_tenant_id(
    tenant_identifier: str,
    db: AsyncSession
) -> int | None:
    """
    Resolver tenant_id desde identifier (subdomain o ID)
    
    Args:
        tenant_identifier: Subdomain o tenant ID
        db: Database session
        
    Returns:
        Tenant ID o None si no existe
    """
    from app.models.tenant import Tenant
    
    # Si es número, asumir que es ID directo
    if tenant_identifier.isdigit():
        tenant_id = int(tenant_identifier)
        result = await db.execute(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.status == "active"
            )
        )
        tenant = result.scalar_one_or_none()
        return tenant.id if tenant else None
    
    # Si no, buscar por subdomain
    result = await db.execute(
        select(Tenant).where(
            Tenant.subdomain == tenant_identifier,
            Tenant.status == "active"
        )
    )
    tenant = result.scalar_one_or_none()
    return tenant.id if tenant else None


async def validate_tenant_active(tenant_id: int, db: AsyncSession) -> bool:
    """
    Validar que tenant esté activo y con licencia vigente
    
    Args:
        tenant_id: Tenant ID
        db: Database session
        
    Returns:
        True si tenant es válido
        
    Raises:
        HTTPException si tenant inactivo o licencia vencida
    """
    from app.models.tenant import Tenant
    from app.models.license import License
    from datetime import datetime
    
    result = await db.execute(
        select(Tenant, License).join(
            License, Tenant.id == License.tenant_id
        ).where(Tenant.id == tenant_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    tenant, license = row
    
    # Verificar estado del tenant
    if tenant.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant suspendido. Contacte a soporte."
        )
    
    # Verificar licencia
    if license.expires_at and license.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Licencia vencida. Renueve su suscripción."
        )
    
    return True


def get_current_tenant_id() -> int:
    """
    Obtener tenant_id del contexto actual
    
    Returns:
        Tenant ID
        
    Raises:
        HTTPException si no hay tenant en contexto
    """
    tenant_id = TenantContext.get_tenant_id()
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant no identificado. Incluya header X-Tenant-ID o use subdominio."
        )
    return tenant_id


def apply_tenant_filter(query, model):
    """
    Aplicar filtro de tenant_id a query SQLAlchemy
    
    Args:
        query: SQLAlchemy query
        model: Model class con tenant_id
        
    Returns:
        Query con filtro aplicado
    """
    tenant_id = TenantContext.get_tenant_id()
    if tenant_id is not None and hasattr(model, "tenant_id"):
        return query.where(model.tenant_id == tenant_id)
    return query


class TenantScopedQuery:
    """
    Mixin para queries tenant-scoped automáticas
    Uso en repositories/services
    """
    
    @staticmethod
    def scope_query(query, model):
        """Apply tenant scope to query"""
        return apply_tenant_filter(query, model)
    
    @staticmethod
    def get_tenant_filter(model):
        """Get tenant filter condition"""
        tenant_id = TenantContext.get_tenant_id()
        if tenant_id is not None and hasattr(model, "tenant_id"):
            return model.tenant_id == tenant_id
        return True  # No filter for global models
