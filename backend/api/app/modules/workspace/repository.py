from typing import Protocol
from uuid import UUID

from sqlalchemy import Select, false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import WorkspaceRecord
from app.modules.identity.domain import DataScope, Permission, Principal
from app.modules.workspace.domain import (
    ScopedWorkspaceRecord,
    WorkspaceArea,
    WorkspaceRecordResponse,
)


def scoped_workspace_statement(
    principal: Principal,
    area: WorkspaceArea,
    record_id: UUID | None = None,
) -> Select[WorkspaceRecord]:
    statement = select(WorkspaceRecord).where(WorkspaceRecord.area == area.value)
    if record_id is not None:
        statement = statement.where(WorkspaceRecord.record_id == record_id)
    if Permission.ALL_BUSINESS_READ in principal.permissions:
        return statement

    if area is WorkspaceArea.OPERATIONS:
        if not principal.scope.store_ids:
            return statement.where(false())
        return statement.where(WorkspaceRecord.store_id.in_(principal.scope.store_ids))

    clauses = [
        WorkspaceRecord.assignee_id == principal.user_id,
        WorkspaceRecord.owner_id == principal.user_id,
    ]
    if area is WorkspaceArea.PROCUREMENT and principal.scope.organization_ids:
        clauses.append(WorkspaceRecord.organization_id.in_(principal.scope.organization_ids))
    if principal.scope.team_ids:
        clauses.append(WorkspaceRecord.team_id.in_(principal.scope.team_ids))
    if area is WorkspaceArea.PROCUREMENT and principal.scope.store_ids:
        clauses.append(WorkspaceRecord.store_id.in_(principal.scope.store_ids))
    return statement.where(or_(*clauses) if clauses else false())


class WorkspaceRepository(Protocol):
    async def list_scoped(
        self, principal: Principal, area: WorkspaceArea
    ) -> list[ScopedWorkspaceRecord]: ...

    async def get_scoped(
        self, principal: Principal, area: WorkspaceArea, record_id: UUID
    ) -> ScopedWorkspaceRecord | None: ...


class InMemoryWorkspaceRepository:
    def __init__(self, records: list[ScopedWorkspaceRecord] | None = None) -> None:
        self.records = records or []

    async def list_scoped(
        self, principal: Principal, area: WorkspaceArea
    ) -> list[ScopedWorkspaceRecord]:
        return [
            record
            for record in self.records
            if record.area == area and self._allowed(principal, record)
        ]

    async def get_scoped(
        self, principal: Principal, area: WorkspaceArea, record_id: UUID
    ) -> ScopedWorkspaceRecord | None:
        return next(
            (
                record
                for record in self.records
                if record.area == area
                and record.response.record_id == record_id
                and self._allowed(principal, record)
            ),
            None,
        )

    @staticmethod
    def _allowed(principal: Principal, record: ScopedWorkspaceRecord) -> bool:
        if Permission.ALL_BUSINESS_READ in principal.permissions:
            return True
        store_match = principal.scope.store_ids.intersection(record.scope.store_ids)
        if record.area is WorkspaceArea.OPERATIONS:
            return bool(store_match)
        if principal.user_id in {record.assignee_id, record.owner_id}:
            return True
        team_match = principal.scope.team_ids.intersection(record.scope.team_ids)
        if record.area is WorkspaceArea.CREATIVE:
            return bool(team_match)
        organization_match = principal.scope.organization_ids.intersection(
            record.scope.organization_ids
        )
        return bool(team_match or store_match or organization_match)


class SqlAlchemyWorkspaceRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_scoped(
        self, principal: Principal, area: WorkspaceArea
    ) -> list[ScopedWorkspaceRecord]:
        async with self._session_factory() as session:
            records = (await session.scalars(scoped_workspace_statement(principal, area))).all()
        return [self._to_domain(record) for record in records]

    async def get_scoped(
        self, principal: Principal, area: WorkspaceArea, record_id: UUID
    ) -> ScopedWorkspaceRecord | None:
        async with self._session_factory() as session:
            record = await session.scalar(scoped_workspace_statement(principal, area, record_id))
        return self._to_domain(record) if record else None

    @staticmethod
    def _to_domain(record: WorkspaceRecord) -> ScopedWorkspaceRecord:
        return ScopedWorkspaceRecord(
            response=WorkspaceRecordResponse(
                record_id=record.record_id,
                store_id=record.store_id,
                record_type=record.record_type,
                title=record.title,
                status=record.status,
                updated_at=record.updated_at,
                summary=record.public_summary,
            ),
            area=WorkspaceArea(record.area),
            assignee_id=record.assignee_id,
            owner_id=record.owner_id,
            scope=DataScope(
                organization_ids=frozenset(
                    [record.organization_id] if record.organization_id else []
                ),
                team_ids=frozenset([record.team_id] if record.team_id else []),
                store_ids=frozenset([record.store_id] if record.store_id else []),
            ),
        )
