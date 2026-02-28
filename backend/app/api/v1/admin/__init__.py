"""
Admin API Router
Rutas administrativas solo para superadmin
"""
from fastapi import APIRouter
from app.api.v1.admin import quote_items, tenants

router = APIRouter()

# Registrar sub-routers
router.include_router(quote_items.router, tags=["Admin - Quote Items"])
router.include_router(tenants.router, tags=["Admin - Tenants"])
