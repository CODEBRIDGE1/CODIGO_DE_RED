"""
Audit Logging Core
Middleware y utilities para registro automático de eventos
"""
import json
import hashlib
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path → (module_key, action, entity_type) mapping helpers
# ---------------------------------------------------------------------------

_SINGULAR = {
    'companies': 'company',
    'projects': 'project',
    'users': 'user',
    'quotes': 'quote',
    'auth': 'session',
    'compliance': 'compliance',
    'obligations': 'obligation',
    'evidences': 'evidence',
    'tasks': 'task',
    'documents': 'document',
    'tenants': 'tenant',
    'quote-items': 'quote_item',
    'security-levels': 'security_level',
    'audit-logs': 'audit_log',
}

_METHOD_ACTION = {
    'POST': 'create',
    'PUT': 'update',
    'PATCH': 'update',
    'DELETE': 'delete',
}

# Paths that never need to be logged
_SKIP_PATHS = {
    '/', '/health', '/docs', '/redoc', '/openapi.json',
    '/api/v1/health', '/api/v1/auth/me', '/api/v1/auth/refresh',
}


def _extract_module_action(method: str, path: str) -> Tuple[str, str, str, Optional[int]]:
    """
    Devuelve (module_key, action, entity_type, entity_id) desde el método HTTP y path.
    """
    # Strip prefix
    p = path.lstrip('/')
    if p.startswith('api/v1/'):
        p = p[7:]
    if p.startswith('admin/'):
        p = p[6:]

    parts = [x for x in p.split('/') if x]
    if not parts:
        return 'system', method.lower(), 'endpoint', None

    module = parts[0]  # e.g. 'companies', 'auth', 'projects'

    # Detect numeric entity_id
    entity_id: Optional[int] = None
    for part in parts[1:]:
        if part.isdigit():
            entity_id = int(part)
            break

    # Sub-action from path (e.g. auth/login, auth/logout)
    if method == 'POST' and len(parts) > 1 and not parts[1].isdigit():
        action = parts[1]  # login, logout, evidences, comments…
    else:
        action = _METHOD_ACTION.get(method, method.lower())

    entity_type = _SINGULAR.get(module, module.rstrip('s'))
    return module, action, entity_type, entity_id


def _decode_token_safe(token: str) -> Optional[Dict]:
    """Decodifica un JWT sin lanzar excepciones."""
    try:
        from jose import jwt, JWTError
        from app.core.config import settings
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        return None


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
    Middleware ASGI que registra automáticamente todas las operaciones de escritura
    (POST, PUT, PATCH, DELETE) en la tabla audit_logs.
    Solo registra respuestas exitosas (2xx). Los errores del cliente (4xx) y del
    servidor (5xx) no se registran como acciones de auditoría.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        method = request.method
        path = request.url.path

        # Generar contexto del request (siempre, para que get_audit_context funcione)
        request_id = str(uuid.uuid4())
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        scope["audit_context"] = {
            "request_id": request_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        # No loguear GETs ni rutas de sistema
        if method in ("GET", "HEAD", "OPTIONS") or path in _SKIP_PATHS:
            await self.app(scope, receive, send)
            return

        # Capturar el status code de la respuesta
        status_code = [200]

        async def capture_send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message.get("status", 200)
            await send(message)

        await self.app(scope, receive, capture_send)

        # Solo loguear operaciones exitosas
        if status_code[0] >= 400:
            return

        # Decodificar JWT para obtener user_id y tenant_id
        user_id: Optional[int] = None
        tenant_id: Optional[int] = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = _decode_token_safe(auth_header[7:])
            if payload:
                try:
                    user_id = int(payload["sub"])
                    tenant_id = payload.get("tenant_id")
                except (KeyError, TypeError, ValueError):
                    pass

        # Mapear path → módulo / acción
        module_key, action, entity_type, entity_id = _extract_module_action(method, path)

        # Escribir en audit_logs de forma asíncrona con su propia sesión
        try:
            async with AsyncSessionLocal() as db:
                await log_audit_event(
                    db=db,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    module_key=module_key,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    after_data={"path": path, "method": method, "status": status_code[0]},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                )
                await db.commit()
        except Exception as exc:
            logger.warning(f"[AuditMiddleware] No se pudo registrar evento: {exc}")


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
