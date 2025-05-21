# filepath: c:\Users\sprim\FocusAreas\Projects\Dev\vibeconomics\backend\src\app\api\main.py
from fastapi import APIRouter

from app.entrypoints.api.routes import items, login, private, users, utils # Adjusted import
from app.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
