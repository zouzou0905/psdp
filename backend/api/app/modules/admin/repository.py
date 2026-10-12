from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import AiFeedbackRecord, GovernanceErrorRecord
from app.modules.admin.domain import (
    AiFeedback,
    ErrorCategory,
    ErrorRecord,
    FeedbackStatus,
    RecordStatus,
    Severity,
)


class AdminRepository(Protocol):
    async def append_error(self, error: ErrorRecord) -> None: ...

    async def list_errors(self, limit: int) -> list[ErrorRecord]: ...

    async def list_ai_feedback(self, limit: int) -> list[AiFeedback]: ...


class InMemoryAdminRepository:
    def __init__(
        self,
        errors: list[ErrorRecord] | None = None,
        feedback: list[AiFeedback] | None = None,
    ) -> None:
        self.errors = errors or []
        self.feedback = feedback or []

    async def append_error(self, error: ErrorRecord) -> None:
        self.errors.insert(0, error)

    async def list_errors(self, limit: int) -> list[ErrorRecord]:
        return self.errors[:limit]

    async def list_ai_feedback(self, limit: int) -> list[AiFeedback]:
        return self.feedback[:limit]


class SqlAlchemyAdminRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def append_error(self, error: ErrorRecord) -> None:
        async with self._session_factory.begin() as session:
            session.add(
                GovernanceErrorRecord(
                    error_id=error.error_id,
                    category=error.category.value,
                    severity=error.severity.value,
                    status=error.status.value,
                    module=error.module,
                    task_id=error.task_id,
                    run_id=error.run_id,
                    action_id=error.action_id,
                    summary=error.summary,
                    details={},
                    occurred_at=error.occurred_at,
                    resolved_at=error.resolved_at,
                    trace_id=error.trace_id,
                )
            )

    async def list_errors(self, limit: int) -> list[ErrorRecord]:
        async with self._session_factory() as session:
            records = (
                await session.scalars(
                    select(GovernanceErrorRecord)
                    .order_by(desc(GovernanceErrorRecord.occurred_at))
                    .limit(limit)
                )
            ).all()
        return [
            ErrorRecord(
                error_id=item.error_id,
                category=ErrorCategory(item.category),
                severity=Severity(item.severity),
                status=RecordStatus(item.status),
                module=item.module,
                task_id=item.task_id,
                run_id=item.run_id,
                action_id=item.action_id,
                summary=item.summary,
                occurred_at=item.occurred_at,
                resolved_at=item.resolved_at,
                trace_id=item.trace_id,
            )
            for item in records
        ]

    async def list_ai_feedback(self, limit: int) -> list[AiFeedback]:
        async with self._session_factory() as session:
            records = (
                await session.scalars(
                    select(AiFeedbackRecord)
                    .order_by(desc(AiFeedbackRecord.created_at))
                    .limit(limit)
                )
            ).all()
        return [
            AiFeedback(
                feedback_id=item.feedback_id,
                task_id=item.task_id,
                run_id=item.run_id,
                capability_id=item.capability_id,
                capability_release_id=item.capability_release_id,
                submitted_by=item.submitted_by,
                feedback_type=item.feedback_type,
                summary=item.summary,
                status=FeedbackStatus(item.status),
                created_at=item.created_at,
            )
            for item in records
        ]
