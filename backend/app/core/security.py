import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import time

from app.core.config import get_settings
from app.core.exceptions import ServiceConfigurationError

ALGORITHM = "HS256"


def _get_signing_secret() -> str:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise ServiceConfigurationError(
            "JWT_SECRET_KEY is missing. Auth features are unavailable until it is configured."
        )
    return settings.jwt_secret_key


def create_access_token(subject: str, session_id: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_in = expires_minutes or settings.access_token_expire_minutes
    payload = {
        "sub": subject,
        "session_id": session_id,
        "token_type": "access",
        "exp": int((datetime.now(UTC) + timedelta(minutes=expire_in)).timestamp()),
    }
    return _encode_jwt(payload)


def create_refresh_token(subject: str, session_id: str, expires_days: int | None = None) -> str:
    settings = get_settings()
    expire_in = expires_days or settings.refresh_token_expire_days
    payload = {
        "sub": subject,
        "session_id": session_id,
        "token_type": "refresh",
        "exp": int((datetime.now(UTC) + timedelta(days=expire_in)).timestamp()),
    }
    return _encode_jwt(payload)


def decode_token(token: str) -> dict[str, object]:
    try:
        return _decode_jwt(token)
    except Exception as exc:
        raise ServiceConfigurationError("Invalid or expired token.") from exc


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_state_token(data: dict[str, str]) -> str:
    payload = {"data": data, "ts": int(time.time())}
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(
        _get_signing_secret().encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    return ".".join(
        (
            base64.urlsafe_b64encode(body).decode("utf-8").rstrip("="),
            base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("="),
        )
    )


def parse_state_token(token: str, max_age_seconds: int = 900) -> dict[str, str]:
    try:
        payload_part, signature_part = token.split(".", maxsplit=1)
        body = base64.urlsafe_b64decode(payload_part + "=" * (-len(payload_part) % 4))
        signature = base64.urlsafe_b64decode(signature_part + "=" * (-len(signature_part) % 4))
        expected = hmac.new(
            _get_signing_secret().encode("utf-8"),
            body,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(signature, expected):
            raise ServiceConfigurationError("OAuth state is invalid or expired.")
        payload = json.loads(body.decode("utf-8"))
        if int(time.time()) - int(payload["ts"]) > max_age_seconds:
            raise ServiceConfigurationError("OAuth state is invalid or expired.")
        return payload["data"]
    except Exception as exc:
        if isinstance(exc, ServiceConfigurationError):
            raise
        raise ServiceConfigurationError("OAuth state is invalid or expired.") from exc


def _urlsafe_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _encode_jwt(payload: dict[str, object]) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    encoded_header = _urlsafe_b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    encoded_payload = _urlsafe_b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    message = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(_get_signing_secret().encode("utf-8"), message, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_urlsafe_b64encode(signature)}"


def _decode_jwt(token: str) -> dict[str, object]:
    encoded_header, encoded_payload, encoded_signature = token.split(".", maxsplit=2)
    message = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(
        _get_signing_secret().encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()
    provided_signature = _urlsafe_b64decode(encoded_signature)
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise ServiceConfigurationError("Invalid or expired token.")
    payload = json.loads(_urlsafe_b64decode(encoded_payload).decode("utf-8"))
    if int(payload["exp"]) < int(datetime.now(UTC).timestamp()):
        raise ServiceConfigurationError("Invalid or expired token.")
    return payload
