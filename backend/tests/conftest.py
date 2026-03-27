import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/callback")
os.environ.setdefault("IMAGE_GENERATION_ENABLED", "false")

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import AuthSession, User  # noqa: E402


@pytest.fixture()
def db_session(tmp_path: Path) -> Session:
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_context(db_session: Session) -> tuple[dict[str, str], User]:
    user = User(
        email="owner@example.com",
        full_name="Owner User",
        picture_url=None,
        provider_subject="google-owner-1",
        provider="google",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    session = AuthSession(user_id=user.id, refresh_token_hash="seed-refresh")
    db_session.add(session)
    db_session.commit()
    token = create_access_token(user.id, session.id)
    return {"Authorization": f"Bearer {token}"}, user
