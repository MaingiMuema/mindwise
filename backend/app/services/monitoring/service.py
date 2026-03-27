from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import LogEntry, UsageStat


class DiagnosticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        *,
        level: str,
        event: str,
        message: str,
        job_id: str | None = None,
        scene_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> LogEntry:
        entry = LogEntry(
            job_id=job_id,
            scene_id=scene_id,
            level=level.upper(),
            event=event,
            message=message,
            payload_json=payload or {},
            created_at=datetime.now(UTC),
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def record_usage(
        self,
        *,
        provider: str,
        metric_name: str,
        metric_value: float,
        unit: str = "count",
        user_id: str | None = None,
        project_id: str | None = None,
        job_id: str | None = None,
    ) -> UsageStat:
        usage = UsageStat(
            user_id=user_id,
            project_id=project_id,
            job_id=job_id,
            provider=provider,
            metric_name=metric_name,
            metric_value=metric_value,
            unit=unit,
            recorded_at=datetime.now(UTC),
        )
        self.db.add(usage)
        self.db.flush()
        return usage
