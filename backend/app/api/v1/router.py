"""API V1 Router"""
from fastapi import APIRouter
# from app.api.v1.endpoints import auth, companies

api_router = APIRouter()

# Temporalmente comentado hasta crear los endpoints
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])

@api_router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api"}
