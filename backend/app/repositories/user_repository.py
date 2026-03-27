from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuthSession, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_provider_subject(self, provider_subject: str) -> User | None:
        return self.db.scalar(select(User).where(User.provider_subject == provider_subject))

    def upsert_google_user(self, profile: dict[str, str | None]) -> User:
        user = self.get_by_provider_subject(profile["sub"] or "")
        if user is None and profile.get("email"):
            user = self.get_by_email(profile["email"])

        if user is None:
            user = User(
                email=profile["email"] or "",
                full_name=profile.get("name"),
                picture_url=profile.get("picture"),
                provider_subject=profile["sub"] or "",
                provider="google",
                is_active=True,
            )
            self.db.add(user)
        else:
            user.email = profile["email"] or user.email
            user.full_name = profile.get("name") or user.full_name
            user.picture_url = profile.get("picture") or user.picture_url
            user.provider_subject = profile["sub"] or user.provider_subject
            user.provider = "google"

        self.db.flush()
        return user

    def get_session_by_hash(self, refresh_token_hash: str) -> AuthSession | None:
        return self.db.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == refresh_token_hash)
        )
