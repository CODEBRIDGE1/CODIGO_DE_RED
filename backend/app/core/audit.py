"""
Audit Logging Core
Middleware y utilities para registro automático de eventos
"""
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.db.session import AsyncSessionLocal


async def log_audit_event(
    db: AsyncSession,
    tenant_id: Optional[int],
    user_id: Optional[int],
    module_key: str,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    before_data: Optional[Dict[str, Any]] = None,
    after_data: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Registrar evento de auditoría
    
    Args:
        db: Database session
        tenant_id: ID del tenant (None para eventos globales)
        user_id: ID del usuario (None para eventos del sistema)
        module_key: Clave del módulo (ej: "companies", "auth")
        action: Acción realizada (ej: "create", "update", "delete", "login")
        entity_type: Tipo de entidad afectada (ej: "company", "user")
        entity_id: ID de la entidad afectada
        before_data: Estado antes del cambio (para updates)
        after_data: Estado después del cambio
        ip_address: IP del cliente
        user_agent: User agent del cliente
        request_id: ID del request para tracing
    """
    from app.models.audit_log import AuditLog
    
    # Redactar datos sensibles (passwords, tokens, etc.)
    if before_data:
        before_data = redact_sensitive_data(before_data)
    if after_data:
        after_data = redact_sensitive_data(after_data)
    
    audit_log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        module_key=module_key,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_data=before_data,
        after_data=after_data,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        created_at=datetime.utcnow()
    )
    
    db.add(audit_log)
    # No commit aquí - se hará en el contexto del request


def redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redactar campos sensibles antes de loguear
    
    Args:
        data: Diccionario con datos
        
    Returns:
        Diccionario con campos sensibles redactados
    """
    sensitive_fields = [
        "password",
        "hashed_password",
        "secret_key",
        "access_token",
        "refresh_token",
        "api_key",
        "token",
        "ssn",
        "credit_card",
    ]
    
    redacted = data.copy()
    
    for field in sensitive_fields:
        if field in redacted:
            redacted[field] = "***REDACTED***"
    
    return redacted


def generate_data_hash(data: Dict[str, Any]) -> str:
    """
    Generar hash SHA256 de datos para integridad
    
    Args:
        data: Diccionario con datos
        
    Returns:
        Hash hexadecimal
    """
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


async def log_auth_event(
    db: AsyncSession,
    action: str,
    user_id: Optional[int],
    email: str,
    success: bool,
    ip_address: str,
    user_agent: str,
    request_id: str,
    reason: Optional[str] = None
) -> None:
    """
    Registrar evento de autenticación
    
    Args:
        db: Database session
        action: Tipo de evento (login, logout, refresh, failed_login)
        user_id: ID del usuario (None si login falló)
        email: Email del intento
        success: Si la acción fue exitosa
        ip_address: IP del cliente
        user_agent: User agent
        request_id: Request ID
        reason: Razón de fallo (si aplica)
    """
    await log_audit_event(
        db=db,
        tenant_id=None,  # Auth events son globales
        user_id=user_id,
        module_key="auth",
        action=action,
        entity_type="user",
        entity_id=user_id,
        after_data={
            "email": email,
            "success": success,
            "reason": reason
        },
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id
    )


async def log_file_operation(
    db: AsyncSession,
    tenant_id: int,
    user_id: int,
    action: str,
    file_key: str,
    filename: str,
    size_bytes: int,
    ip_address: str,
    user_agent: str,
    request_id: str
) -> None:
    """
    Registrar operación con archivos
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        user_id: Usuario que realizó la acción
        action: upload, download, delete
        file_key: Key del archivo en MinIO
        filename: Nombre original del archivo
        size_bytes: Tamaño en bytes
        ip_address: IP del cliente
        user_agent: User agent
        request_id: Request ID
    """
    await log_audit_event(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        module_key="evidences",
        action=action,
        entity_type="file",
        after_data={
            "file_key": file_key,
            "filename": filename,
            "size_bytes": size_bytes
        },
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id
    )


class AuditMiddleware:
    """
    Middleware para loguear automáticamente requests/responses
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extraer info del request
        request = Request(scope, receive)
        
        # Generar request_id único
        import uuid
        request_id = str(uuid.uuid4())
        scope["request_id"] = request_id
        
        # Extraer IP y user agent
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Almacenar para uso en endpoints
        scope["audit_context"] = {
            "request_id": request_id,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        await self.app(scope, receive, send)


def get_audit_context(request: Request) -> Dict[str, str]:
    """
    Obtener contexto de auditoría del request
    
    Args:
        request: FastAPI Request
        
    Returns:
        Dict con request_id, ip_address, user_agent
    """
    if hasattr(request.scope, "audit_context"):
        return request.scope["audit_context"]
    
    # Fallback si middleware no está activo
    import uuid
    return {
        "request_id": str(uuid.uuid4()),
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }


async def log_entity_change(
    db: AsyncSession,
    request: Request,
    user_id: int,
    module_key: str,
    action: str,
    entity_type: str,
    entity_id: int,
    before: Optional[Dict] = None,
    after: Optional[Dict] = None
) -> None:
    """
    Helper para loguear cambios en entidades desde endpoints
    
    Usage:
        await log_entity_change(
            db=db,
            request=request,
            user_id=current_user.id,
            module_key="companies",
            action="update",
            entity_type="company",
            entity_id=company.id,
            before={"name": "Old Name"},
            after={"name": "New Name"}
        )
    """
    audit_ctx = get_audit_context(request)
    tenant_id = TenantContext.get_tenant_id()
    
    await log_audit_event(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        module_key=module_key,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_data=before,
        after_data=after,
        ip_address=audit_ctx["ip_address"],
        user_agent=audit_ctx["user_agent"],
        request_id=audit_ctx["request_id"]
    )
