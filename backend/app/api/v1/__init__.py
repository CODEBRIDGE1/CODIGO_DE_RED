"""
API v1 Router
Agrega todos los routers de la API v1
"""
from fastapi import APIRouter
from app.api.v1 import auth, users, companies, documents, compliance, projects, quotes
from app.api.v1.admin import quote_items

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

# Projects endpoints
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])

# Quotes endpoints (Tenant)
api_router.include_router(quotes.router, prefix="/quotes", tags=["Quotes"])

# Admin endpoints
api_router.include_router(quote_items.router, prefix="/admin/quote-items", tags=["Admin - Quote Items"])
