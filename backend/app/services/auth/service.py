from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, ServiceConfigurationError
from app.core.security import (
    build_state_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    parse_state_token,
)
from app.models import AuthSession, User
from app.repositories import UserRepository
from app.schemas.auth import TokenPair


class GoogleAuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.users = UserRepository(db)

    def build_authorization_url(self, redirect_hint: str | None = None) -> tuple[str, str]:
        if not self.settings.oauth_enabled:
            raise ServiceConfigurationError(
                "Google OAuth is not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI."
            )

        state = build_state_token(
            {"nonce": str(uuid4()), "redirect_hint": redirect_hint or ""}
        )
        params = urlencode(
            {
                "client_id": self.settings.google_client_id,
                "redirect_uri": self.settings.google_redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
        )
        return f"{self.settings.google_auth_base_url}?{params}", state

    def authenticate(
        self,
        *,
        code: str,
        state: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, TokenPair]:
        parse_state_token(state)
        token_payload = self._exchange_code(code)
        profile = self._fetch_profile(token_payload)
        user = self.users.upsert_google_user(profile)

        session = AuthSession(
            user_id=user.id,
            provider="google",
            refresh_token_hash="pending",
            access_token_expires_at=datetime.now(UTC)
            + timedelta(minutes=self.settings.access_token_expire_minutes),
            user_agent=user_agent,
            ip_address=ip_address,
            state_nonce=profile.get("sub"),
            last_used_at=datetime.now(UTC),
        )
        self.db.add(session)
        self.db.flush()

        access_token = create_access_token(user.id, session.id)
        refresh_token = create_refresh_token(user.id, session.id)
        session.refresh_token_hash = hash_token(refresh_token)
        self.db.commit()
        self.db.refresh(user)

        return user, TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

    def refresh(self, refresh_token: str) -> tuple[User, TokenPair]:
        payload = decode_token(refresh_token)
        if payload.get("token_type") != "refresh":
            raise ServiceConfigurationError("Refresh token is invalid.")

        session = self.users.get_session_by_hash(hash_token(refresh_token))
        if session is None or session.id != payload.get("session_id"):
            raise ServiceConfigurationError("Refresh session could not be found.")

        user = self.db.get(User, payload.get("sub"))
        if user is None or not user.is_active:
            raise ServiceConfigurationError("User is not active.")

        access_token = create_access_token(user.id, session.id)
        new_refresh_token = create_refresh_token(user.id, session.id)
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.last_used_at = datetime.now(UTC)
        session.access_token_expires_at = datetime.now(UTC) + timedelta(
            minutes=self.settings.access_token_expire_minutes
        )
        self.db.commit()

        return user, TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

    def _exchange_code(self, code: str) -> dict:
        response = httpx.post(
            self.settings.google_token_url,
            data={
                "code": code,
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "redirect_uri": self.settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=45.0,
        )
        response.raise_for_status()
        return response.json()

    def _fetch_profile(self, token_payload: dict) -> dict[str, str | None]:
        if token_payload.get("id_token"):
            response = httpx.get(
                self.settings.google_token_info_url,
                params={"id_token": token_payload["id_token"]},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

        if token_payload.get("access_token"):
            response = httpx.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token_payload['access_token']}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

        raise ExternalServiceError("Google OAuth response did not include an ID token or access token.")
