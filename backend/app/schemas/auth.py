from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class AuthUrlResponse(BaseModel):
    authorization_url: str
    state: str


class AuthCallbackRequest(BaseModel):
    code: str
    state: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserRead(TimestampedRead):
    email: str
    full_name: str | None = None
    picture_url: str | None = None
    provider: str


class AuthResponse(BaseModel):
    user: UserRead
    tokens: TokenPair
