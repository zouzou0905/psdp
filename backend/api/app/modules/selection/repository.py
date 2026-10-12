from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, false, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import (
    SelectionAiTask,
    SelectionCompetitorVersion,
    SelectionFinalVersion,
    SelectionListingDraftVersion,
    SelectionProfitReviewVersion,
    SelectionQuotationVersion,
    SelectionRecord,
)
from app.modules.identity.domain import Permission, Principal
from app.modules.selection.domain import (
    CompetitorInput,
    FinalDecision,
    QuotationUpsertRequest,
    SelectionStage,
)


class SelectionRevisionConflictError(Exception):
    pass


def _scoped(
    statement: Select[SelectionRecord], principal: Principal
) -> Select[SelectionRecord]:
    if Permission.ALL_BUSINESS_READ in principal.permissions:
        return statement
    if not principal.scope.store_ids:
        return statement.where(false())
    return statement.where(SelectionRecord.store_id.in_(principal.scope.store_ids))


class SqlAlchemySelectionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_records(self, principal: Principal) -> list[SelectionRecord]:
        async with self._session_factory() as session:
            statement = _scoped(
                select(SelectionRecord).order_by(SelectionRecord.updated_at.desc()), principal
            )
            return list((await session.scalars(statement)).all())

    async def get_record(
        self, principal: Principal, selection_id: UUID
    ) -> SelectionRecord | None:
        async with self._session_factory() as session:
            return await session.scalar(
                _scoped(
                    select(SelectionRecord).where(
                        SelectionRecord.selection_id == selection_id
                    ),
                    principal,
                )
            )

    async def get_quotation(
        self, principal: Principal, selection_id: UUID
    ) -> SelectionQuotationVersion | None:
        async with self._session_factory() as session:
            if await self._get_scoped_record(session, principal, selection_id) is None:
                return None
            return await session.scalar(
                select(SelectionQuotationVersion)
                .where(SelectionQuotationVersion.selection_id == selection_id)
                .order_by(SelectionQuotationVersion.version.desc())
                .limit(1)
            )

    async def save_quotation(
        self,
        principal: Principal,
        selection_id: UUID,
        payload: QuotationUpsertRequest,
    ) -> tuple[SelectionRecord, SelectionQuotationVersion] | None:
        async with self._session_factory.begin() as session:
            record = await self._lock_scoped_record(session, principal, selection_id)
            if record is None:
                return None
            if record.revision != payload.expected_revision:
                raise SelectionRevisionConflictError
            version = (
                await session.scalar(
                    select(func.max(SelectionQuotationVersion.version)).where(
                        SelectionQuotationVersion.selection_id == selection_id
                    )
                )
                or 0
            ) + 1
            quotation = SelectionQuotationVersion(
                selection_id=selection_id,
                version=version,
                supplier_name=payload.supplier_name,
                unit_cost=payload.unit_cost,
                currency=payload.currency,
                value_status=payload.value_status.value,
                moq=payload.moq,
                lead_time_days=payload.lead_time_days,
                freight_per_unit=payload.freight_per_unit,
                other_cost_per_unit=payload.other_cost_per_unit,
                target_price=payload.target_price,
                notes=payload.notes,
                submission_status="submitted",
                recorded_by=principal.user_id,
            )
            session.add(quotation)
            record.stage = SelectionStage.QUOTED.value
            record.revision += 1
            record.updated_at = func.now()
            await session.flush()
            await session.refresh(quotation)
            await session.refresh(record)
            return record, quotation

    async def get_profit_review(
        self, principal: Principal, selection_id: UUID
    ) -> SelectionProfitReviewVersion | None:
        async with self._session_factory() as session:
            record = await self._get_scoped_record(session, principal, selection_id)
            if record is None or record.stage in {
                SelectionStage.SOURCED.value,
                SelectionStage.QUOTED.value,
            }:
                return None
            return await session.scalar(
                select(SelectionProfitReviewVersion)
                .where(SelectionProfitReviewVersion.selection_id == selection_id)
                .order_by(SelectionProfitReviewVersion.version.desc())
                .limit(1)
            )

    async def get_final_selection(
        self, principal: Principal, selection_id: UUID
    ) -> SelectionFinalVersion | None:
        async with self._session_factory() as session:
            record = await self._get_scoped_record(session, principal, selection_id)
            if record is None or record.stage not in {
                SelectionStage.FINAL_SELECTED.value,
                SelectionStage.FINAL_REJECTED.value,
            }:
                return None
            return await self._latest_final(session, selection_id)

    async def save_final_selection(
        self,
        principal: Principal,
        selection_id: UUID,
        decision: FinalDecision,
        reason: str | None,
        expected_revision: int,
    ) -> tuple[SelectionRecord, SelectionFinalVersion] | None:
        async with self._session_factory.begin() as session:
            record = await self._lock_scoped_record(session, principal, selection_id)
            if record is None:
                return None
            if record.revision != expected_revision:
                raise SelectionRevisionConflictError
            profit = await session.scalar(
                select(SelectionProfitReviewVersion)
                .where(SelectionProfitReviewVersion.selection_id == selection_id)
                .order_by(SelectionProfitReviewVersion.version.desc())
                .limit(1)
            )
            if profit is None or record.stage not in {
                SelectionStage.PROFIT_REVIEWED.value,
                SelectionStage.FINAL_SELECTED.value,
                SelectionStage.FINAL_REJECTED.value,
            }:
                return None
            version = (await self._max_final_version(session, selection_id)) + 1
            final = SelectionFinalVersion(
                selection_id=selection_id,
                version=version,
                profit_review_version=profit.version,
                decision=decision.value,
                reason=reason,
                decided_by=principal.user_id,
            )
            session.add(final)
            record.stage = (
                SelectionStage.FINAL_SELECTED.value
                if decision is FinalDecision.SELECTED
                else SelectionStage.FINAL_REJECTED.value
            )
            record.revision += 1
            record.updated_at = func.now()
            await session.flush()
            await session.refresh(final)
            await session.refresh(record)
            return record, final

    async def save_competitors(
        self,
        principal: Principal,
        selection_id: UUID,
        competitors: Sequence[CompetitorInput],
        expected_revision: int,
    ) -> tuple[SelectionRecord, SelectionFinalVersion, list[SelectionCompetitorVersion]] | None:
        async with self._session_factory.begin() as session:
            record = await self._lock_scoped_record(session, principal, selection_id)
            if record is None:
                return None
            if record.revision != expected_revision:
                raise SelectionRevisionConflictError
            current = await self._latest_final(session, selection_id)
            if current is None or current.decision != FinalDecision.SELECTED.value:
                return None
            next_version = current.version + 1
            final = SelectionFinalVersion(
                selection_id=selection_id,
                version=next_version,
                profit_review_version=current.profit_review_version,
                decision=current.decision,
                reason=current.reason,
                decided_by=principal.user_id,
            )
            session.add(final)
            rows = [
                SelectionCompetitorVersion(
                    selection_id=selection_id,
                    final_version=next_version,
                    position=position,
                    title=item.title,
                    bullets=item.bullets,
                    recorded_by=principal.user_id,
                )
                for position, item in enumerate(competitors, start=1)
            ]
            session.add_all(rows)
            record.revision += 1
            record.updated_at = func.now()
            await session.flush()
            for row in rows:
                await session.refresh(row)
            await session.refresh(final)
            await session.refresh(record)
            return record, final, rows

    async def list_competitors(
        self, principal: Principal, selection_id: UUID
    ) -> tuple[SelectionRecord, SelectionFinalVersion, list[SelectionCompetitorVersion]] | None:
        async with self._session_factory() as session:
            record = await self._get_scoped_record(session, principal, selection_id)
            if record is None:
                return None
            final = await self._latest_final(session, selection_id)
            if final is None:
                return None
            rows = list(
                (
                    await session.scalars(
                        select(SelectionCompetitorVersion)
                        .where(
                            SelectionCompetitorVersion.selection_id == selection_id,
                            SelectionCompetitorVersion.final_version == final.version,
                        )
                        .order_by(SelectionCompetitorVersion.position)
                    )
                ).all()
            )
            return record, final, rows

    async def list_ai_tasks(
        self, principal: Principal, selection_id: UUID
    ) -> list[SelectionAiTask] | None:
        async with self._session_factory() as session:
            if await self._get_scoped_record(session, principal, selection_id) is None:
                return None
            statement = (
                select(SelectionAiTask)
                .where(SelectionAiTask.selection_id == selection_id)
                .order_by(SelectionAiTask.created_at)
            )
            if Permission.LISTING_COPY_READ not in principal.permissions:
                statement = statement.where(
                    SelectionAiTask.task_type != "listing_draft"
                )
            return list(
                (
                    await session.scalars(statement)
                ).all()
            )

    async def get_listing_draft(
        self, principal: Principal, selection_id: UUID
    ) -> SelectionListingDraftVersion | None:
        async with self._session_factory() as session:
            if await self._get_scoped_record(session, principal, selection_id) is None:
                return None
            return await session.scalar(
                select(SelectionListingDraftVersion)
                .where(SelectionListingDraftVersion.selection_id == selection_id)
                .order_by(SelectionListingDraftVersion.version.desc())
                .limit(1)
            )

    async def _get_scoped_record(
        self, session: AsyncSession, principal: Principal, selection_id: UUID
    ) -> SelectionRecord | None:
        return await session.scalar(
            _scoped(
                select(SelectionRecord).where(SelectionRecord.selection_id == selection_id),
                principal,
            )
        )

    async def _lock_scoped_record(
        self, session: AsyncSession, principal: Principal, selection_id: UUID
    ) -> SelectionRecord | None:
        return await session.scalar(
            _scoped(
                select(SelectionRecord)
                .where(SelectionRecord.selection_id == selection_id)
                .with_for_update(),
                principal,
            )
        )

    @staticmethod
    async def _latest_final(
        session: AsyncSession, selection_id: UUID
    ) -> SelectionFinalVersion | None:
        return await session.scalar(
            select(SelectionFinalVersion)
            .where(SelectionFinalVersion.selection_id == selection_id)
            .order_by(SelectionFinalVersion.version.desc())
            .limit(1)
        )

    @staticmethod
    async def _max_final_version(session: AsyncSession, selection_id: UUID) -> int:
        return (
            await session.scalar(
                select(func.max(SelectionFinalVersion.version)).where(
                    SelectionFinalVersion.selection_id == selection_id
                )
            )
            or 0
        )
