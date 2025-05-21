import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.entrypoints.api.main import api_router
from app.config import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "🚀 Welcome to the Vibeconomics API! 🚀",
        "description": "Powering the future of economic vibes, one request at a time.",
        "documentation": "/docs",
        "api_version": settings.API_V1_STR.replace("/", ""),
        "project_name": settings.PROJECT_NAME,
        "status": "✨ Shiny and Operational ✨"
    }

app.include_router(api_router, prefix=settings.API_V1_STR)
