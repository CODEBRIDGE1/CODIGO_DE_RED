"""API V1 Router"""
from fastapi import APIRouter
from app.api.v1 import auth, companies, users, documents, compliance, projects, quotes
from app.api.v1.admin import router as admin_router

api_router = APIRouter()

# Auth & Users
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Companies & Compliance
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance Matrix"])

# Documents
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])

# Projects
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])

# Quotes (Cotizaciones para tenants)
api_router.include_router(quotes.router, prefix="/quotes", tags=["Quotes"])

# Admin (solo superadmin)
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])

@api_router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api"}
