from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    auth_ready: bool
    missing_env_vars: list[str]
    database_backend: str
