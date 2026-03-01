"""
Admin API Router
Rutas administrativas solo para superadmin
"""
from fastapi import APIRouter
from app.api.v1.admin import quote_items, tenants, users, companies, security_levels, quotes

router = APIRouter()

# Registrar sub-routers
router.include_router(quote_items.router, prefix="/quote-items", tags=["Admin - Quote Items"])
router.include_router(quotes.router, prefix="/quotes", tags=["Admin - Quotes"])
router.include_router(tenants.router, prefix="/tenants", tags=["Admin - Tenants"])
router.include_router(users.router, prefix="/users", tags=["Admin - Users"])
router.include_router(companies.router, prefix="/companies", tags=["Admin - Companies"])
router.include_router(security_levels.router, prefix="/security-levels", tags=["Admin - Security Levels"])
