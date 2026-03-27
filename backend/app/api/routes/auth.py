from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.auth import (
    AuthCallbackRequest,
    AuthResponse,
    AuthUrlResponse,
    RefreshTokenRequest,
    UserRead,
)
from app.services.auth import GoogleAuthService

router = APIRouter()


@router.get("/google/login", response_model=AuthUrlResponse)
def google_login(
    redirect_hint: str | None = None,
    db: Session = Depends(get_db),
) -> AuthUrlResponse:
    service = GoogleAuthService(db)
    authorization_url, state = service.build_authorization_url(redirect_hint=redirect_hint)
    return AuthUrlResponse(authorization_url=authorization_url, state=state)


@router.post("/google/callback", response_model=AuthResponse)
def google_callback(
    payload: AuthCallbackRequest,
    request: Request,
    user_agent: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AuthResponse:
    service = GoogleAuthService(db)
    user, tokens = service.authenticate(
        code=payload.code,
        state=payload.state,
        user_agent=user_agent,
        ip_address=request.client.host if request.client else None,
    )
    return AuthResponse(user=UserRead.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=AuthResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    service = GoogleAuthService(db)
    user, tokens = service.refresh(payload.refresh_token)
    return AuthResponse(user=UserRead.model_validate(user), tokens=tokens)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
