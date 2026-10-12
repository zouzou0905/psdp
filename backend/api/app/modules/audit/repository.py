from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import GovernanceAuditLog
from app.modules.audit.domain import AuditEvent, AuditResult
from app.modules.identity.domain import RoleName


class AuditRepository(Protocol):
    async def append(self, event: AuditEvent) -> None: ...

    async def list_recent(self, limit: int = 100) -> list[AuditEvent]: ...


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def append(self, event: AuditEvent) -> None:
        self.events.append(event)

    async def list_recent(self, limit: int = 100) -> list[AuditEvent]:
        return list(reversed(self.events[-limit:]))


class SqlAlchemyAuditRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def append(self, event: AuditEvent) -> None:
        async with self._session_factory.begin() as session:
            session.add(
                GovernanceAuditLog(
                    audit_id=event.audit_id,
                    actor_id=event.actor_id,
                    actor_roles=[role.value for role in event.actor_roles],
                    action=event.action,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    result=event.result.value,
                    trace_id=event.trace_id,
                    occurred_at=event.occurred_at,
                    metadata_summary=event.metadata_summary,
                )
            )

    async def list_recent(self, limit: int = 100) -> list[AuditEvent]:
        async with self._session_factory() as session:
            records = (
                await session.scalars(
                    select(GovernanceAuditLog)
                    .order_by(desc(GovernanceAuditLog.occurred_at))
                    .limit(limit)
                )
            ).all()
        return [
            AuditEvent(
                audit_id=record.audit_id,
                actor_id=record.actor_id,
                actor_roles=tuple(RoleName(role) for role in record.actor_roles),
                action=record.action,
                resource_type=record.resource_type,
                resource_id=record.resource_id,
                result=AuditResult(record.result),
                trace_id=record.trace_id,
                occurred_at=record.occurred_at,
                metadata_summary=record.metadata_summary,
            )
            for record in records
        ]
