from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.system import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/system/readiness", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    settings = get_settings()
    return ReadinessResponse(
        status="ok" if settings.auth_ready else "degraded",
        auth_ready=settings.auth_ready,
        missing_env_vars=settings.missing_env_vars,
        database_backend=settings.database_url.split(":")[0],
    )
