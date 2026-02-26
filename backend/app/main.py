"""
FastAPI Main Application
Punto de entrada de la API
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.audit import AuditMiddleware
from app.db.session import close_db
from app.api.v1 import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events
    """
    # Startup
    logger.info("🚀 Starting Código de Red API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    await close_db()
    logger.info("✓ Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add rate limiting state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================
# Middleware
# ============================================

# Audit Middleware (se ejecuta último)
app.add_middleware(AuditMiddleware)

# Trusted Host (seguridad adicional en producción)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.codigo-red.com", "codigo-red.com", "31.97.210.250", "31.97.210.250:8001", "localhost", "127.0.0.1"]
    )

# CORS (debe ejecutarse primero, por eso se agrega último)
cors_origins = settings.get_cors_origins()

# En desarrollo, permitir todos los orígenes para facilitar pruebas
if settings.is_development:
    logger.info("🌐 CORS: Permitiendo TODOS los orígenes (development mode)")
    cors_origins = ["*"]
else:
    logger.info(f"🌐 CORS: Orígenes permitidos: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"]
)


# ============================================
# Exception Handlers
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler para errores no capturados
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error" if settings.is_production else str(exc),
            "type": "internal_error"
        }
    )


# ============================================
# Routes
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - health check básico
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "online"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint para monitoring/load balancers
    """
    # TODO: Agregar checks de database, redis, minio
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ============================================
# Startup message
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower()
    )
