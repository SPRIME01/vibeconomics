# filepath: c:\Users\sprim\FocusAreas\Projects\Dev\vibeconomics\backend\src\app\api\main.py
from fastapi import APIRouter

from app.config import settings
from app.entrypoints.api.routes import (  # Adjusted import
    items,
    login,
    private,
    users,
    utils,
)

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
