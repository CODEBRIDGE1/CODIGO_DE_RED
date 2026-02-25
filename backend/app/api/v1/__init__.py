"""
API v1 Router
Agrega todos los routers de la API v1
"""
from fastapi import APIRouter
from app.api.v1 import auth, users, companies, documents, compliance, projects

api_router = APIRouter()

# Auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Users endpoints
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Companies endpoints
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])

# Documents endpoints (nested under companies)
api_router.include_router(documents.router, prefix="/companies", tags=["Documents"])

# Compliance endpoints (Matriz de Obligaciones)
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])

# Projects endpoints (Proyectos)
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
