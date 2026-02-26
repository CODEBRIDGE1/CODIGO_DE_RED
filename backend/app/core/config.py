"""
Core Configuration Settings
Pydantic Settings para variables de entorno
"""
from typing import List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application Settings"""
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Código de Red Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Multi-tenant SaaS para gestión de cumplimiento normativo"
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # MinIO / S3
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str = "evidences"
    MINIO_SECURE: bool = False  # True para HTTPS
    MINIO_EXTERNAL_ENDPOINT: str  # Para presigned URLs accesibles desde navegador
    
    # Security / JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:5173"  # URL principal del frontend
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as list, including FRONTEND_URL"""
        origins = []
        
        # Agregar CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            origins.extend([origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()])
        else:
            origins.extend(self.CORS_ORIGINS)
        
        # Agregar FRONTEND_URL si no está ya incluido
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        
        # Eliminar duplicados preservando orden
        seen = set()
        unique_origins = []
        for origin in origins:
            if origin not in seen:
                seen.add(origin)
                unique_origins.append(origin)
        
        return unique_origins
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", 
        ".jpg", ".jpeg", ".png", ".gif",
        ".zip", ".rar", ".csv"
    ]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Observability
    SENTRY_DSN: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


# Singleton settings instance
settings = Settings()
