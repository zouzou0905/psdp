import hashlib
import json
from datetime import UTC, datetime
from typing import Protocol, cast
from uuid import UUID, uuid4

from sqlalchemy import false, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import (
    SelectionExportJob,
    SelectionQuotationVersion,
    SelectionRecord,
    SelectionTableSnapshot,
    SelectionTableSnapshotRow,
    StoreRecord,
)
from app.modules.selection_export.domain import (
    FrozenSnapshot,
    FrozenSnapshotRow,
    GeneratedExportFile,
    SelectionExportCreateRequest,
    SelectionExportStage,
    SelectionExportStatus,
)


class SelectionExportRepository(Protocol):
    async def create_job_with_snapshot(
        self,
        *,
        requested_by: UUID,
        authorization_revision: int,
        payload: SelectionExportCreateRequest,
        effective_store_ids: list[str] | None,
        schema_version: str,
        trace_id: str | None,
        expires_at: datetime,
    ) -> SelectionExportJob: ...

    async def get_owned_job(
        self, export_id: UUID, requested_by: UUID
    ) -> SelectionExportJob | None: ...

    async def get_snapshot(self, snapshot_id: UUID) -> FrozenSnapshot | None: ...

    async def mark_running(self, export_id: UUID) -> None: ...

    async def mark_completed(
        self, export_id: UUID, generated_file: GeneratedExportFile
    ) -> None: ...

    async def mark_failed(self, export_id: UUID, error_code: str, error_message: str) -> None: ...

    async def store_display_names(self, store_ids: list[str]) -> list[str]: ...

    async def authorized_store_ids(
        self, store_ids: set[str], organization_ids: set[str]
    ) -> set[str]: ...


class SqlAlchemySelectionExportRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create_job_with_snapshot(
        self,
        *,
        requested_by: UUID,
        authorization_revision: int,
        payload: SelectionExportCreateRequest,
        effective_store_ids: list[str] | None,
        schema_version: str,
        trace_id: str | None,
        expires_at: datetime,
    ) -> SelectionExportJob:
        async with self._session_factory.begin() as session:
            statement = select(SelectionRecord)
            if effective_store_ids is not None:
                statement = (
                    statement.where(SelectionRecord.store_id.in_(effective_store_ids))
                    if effective_store_ids
                    else statement.where(false())
                )
            if payload.search is not None:
                pattern = f"%{payload.search}%"
                statement = statement.where(
                    or_(
                        SelectionRecord.product_name.ilike(pattern),
                        SelectionRecord.marketplace.ilike(pattern),
                    )
                )
            if payload.marketplace is not None:
                statement = statement.where(
                    SelectionRecord.marketplace == payload.marketplace
                )
            if payload.source_type is not None:
                statement = statement.where(SelectionRecord.source_type == payload.source_type)
            if payload.stage is SelectionExportStage.INITIAL_SELECTION:
                records = list(
                    (
                        await session.scalars(
                            statement.order_by(SelectionRecord.selection_id)
                        )
                    ).all()
                )
                rendered_rows = [self._rendered_row(record) for record in records]
            else:
                latest_submitted = (
                    select(
                        SelectionQuotationVersion.selection_id,
                        func.max(SelectionQuotationVersion.version).label("version"),
                    )
                    .where(
                        SelectionQuotationVersion.submission_status == "submitted"
                    )
                    .group_by(SelectionQuotationVersion.selection_id)
                    .subquery()
                )
                quotation_statement = (
                    statement.add_columns(SelectionQuotationVersion)
                    .join(
                        latest_submitted,
                        latest_submitted.c.selection_id == SelectionRecord.selection_id,
                    )
                    .join(
                        SelectionQuotationVersion,
                        (
                            SelectionQuotationVersion.selection_id
                            == latest_submitted.c.selection_id
                        )
                        & (
                            SelectionQuotationVersion.version
                            == latest_submitted.c.version
                        ),
                    )
                    .order_by(SelectionRecord.selection_id)
                )
                quotation_rows = list((await session.execute(quotation_statement)).all())
                records = [cast(SelectionRecord, row[0]) for row in quotation_rows]
                rendered_rows = [
                    self._quotation_rendered_row(
                        cast(SelectionRecord, row[0]),
                        cast(SelectionQuotationVersion, row[1]),
                    )
                    for row in quotation_rows
                ]
            snapshot_id = uuid4()
            actual_scope = sorted({record.store_id for record in records})
            if effective_store_ids is not None:
                actual_scope = sorted(effective_store_ids)
            filters = payload.filters()
            snapshot_checksum = self._snapshot_checksum(
                payload.stage, schema_version, filters, actual_scope, rendered_rows
            )
            snapshot = SelectionTableSnapshot(
                snapshot_id=snapshot_id,
                stage=payload.stage.value,
                schema_version=schema_version,
                filters_json=filters,
                store_scope_json=actual_scope,
                requested_by=requested_by,
                row_count=len(rendered_rows),
                snapshot_checksum=snapshot_checksum,
            )
            session.add(snapshot)
            # The models intentionally expose no mutable ORM relationship; flush the
            # immutable parent explicitly before inserting its rows and export job.
            await session.flush()
            session.add_all(
                [
                    SelectionTableSnapshotRow(
                        snapshot_id=snapshot_id,
                        row_position=position,
                        selection_id=record.selection_id,
                        selection_revision=record.revision,
                        rendered_row=rendered_row,
                    )
                    for position, (record, rendered_row) in enumerate(
                        zip(records, rendered_rows, strict=True), start=1
                    )
                ]
            )
            job = SelectionExportJob(
                stage=payload.stage.value,
                snapshot_id=snapshot_id,
                schema_version=schema_version,
                filters_json=filters,
                store_scope_json=actual_scope,
                requested_by=requested_by,
                authorization_revision=authorization_revision,
                status=SelectionExportStatus.QUEUED.value,
                row_count=len(rendered_rows),
                trace_id=trace_id,
                expires_at=expires_at,
            )
            session.add(job)
            await session.flush()
            await session.refresh(job)
            return job

    async def get_owned_job(
        self, export_id: UUID, requested_by: UUID
    ) -> SelectionExportJob | None:
        async with self._session_factory() as session:
            return await session.scalar(
                select(SelectionExportJob).where(
                    SelectionExportJob.export_id == export_id,
                    SelectionExportJob.requested_by == requested_by,
                )
            )

    async def get_snapshot(self, snapshot_id: UUID) -> FrozenSnapshot | None:
        async with self._session_factory() as session:
            snapshot = await session.get(SelectionTableSnapshot, snapshot_id)
            if snapshot is None:
                return None
            rows = list(
                (
                    await session.scalars(
                        select(SelectionTableSnapshotRow)
                        .where(SelectionTableSnapshotRow.snapshot_id == snapshot_id)
                        .order_by(SelectionTableSnapshotRow.row_position)
                    )
                ).all()
            )
            return FrozenSnapshot(
                snapshot_id=snapshot.snapshot_id,
                stage=SelectionExportStage(snapshot.stage),
                schema_version=snapshot.schema_version,
                filters=snapshot.filters_json,
                store_scope=list(snapshot.store_scope_json),
                requested_by=snapshot.requested_by,
                row_count=snapshot.row_count,
                snapshot_checksum=snapshot.snapshot_checksum,
                created_at=snapshot.created_at,
                rows=[
                    FrozenSnapshotRow(
                        row_position=row.row_position,
                        selection_id=row.selection_id,
                        selection_revision=row.selection_revision,
                        rendered_row=row.rendered_row,
                    )
                    for row in rows
                ],
            )

    async def mark_running(self, export_id: UUID) -> None:
        await self._update_job(
            export_id,
            status=SelectionExportStatus.RUNNING.value,
            error_code=None,
            error_message=None,
        )

    async def mark_completed(
        self, export_id: UUID, generated_file: GeneratedExportFile
    ) -> None:
        await self._update_job(
            export_id,
            status=SelectionExportStatus.COMPLETED.value,
            file_name=generated_file.file_name,
            file_path=str(generated_file.path),
            file_checksum=generated_file.checksum,
            completed_at=datetime.now(UTC),
        )

    async def mark_failed(self, export_id: UUID, error_code: str, error_message: str) -> None:
        await self._update_job(
            export_id,
            status=SelectionExportStatus.FAILED.value,
            error_code=error_code,
            error_message=error_message[:500],
            completed_at=datetime.now(UTC),
        )

    async def store_display_names(self, store_ids: list[str]) -> list[str]:
        if not store_ids:
            return []
        async with self._session_factory() as session:
            return list(
                (
                    await session.scalars(
                        select(StoreRecord.display_name)
                        .where(StoreRecord.store_id.in_(store_ids))
                        .order_by(StoreRecord.store_id)
                    )
                ).all()
            )

    async def authorized_store_ids(
        self, store_ids: set[str], organization_ids: set[str]
    ) -> set[str]:
        if not store_ids and not organization_ids:
            return set()
        conditions = []
        if store_ids:
            conditions.append(StoreRecord.store_id.in_(store_ids))
        if organization_ids:
            conditions.append(StoreRecord.organization_id.in_(organization_ids))
        async with self._session_factory() as session:
            return set(
                (
                    await session.scalars(
                        select(StoreRecord.store_id).where(or_(*conditions))
                    )
                ).all()
            )

    async def _update_job(self, export_id: UUID, **values: object) -> None:
        async with self._session_factory.begin() as session:
            await session.execute(
                update(SelectionExportJob)
                .where(SelectionExportJob.export_id == export_id)
                .values(**values)
            )

    @staticmethod
    def _rendered_row(record: SelectionRecord) -> dict[str, object]:
        return {
            "selection_id": str(record.selection_id),
            "store_id": record.store_id,
            "marketplace": record.marketplace,
            "product_name": record.product_name,
            "source_type": record.source_type,
            "source_ref": record.source_ref,
            "source_snapshot_ref": record.source_snapshot_ref,
            "source_version": record.source_version,
            "owner_id": str(record.owner_id) if record.owner_id else None,
            "stage": record.stage,
            "revision": record.revision,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    @staticmethod
    def _quotation_rendered_row(
        record: SelectionRecord, quotation: SelectionQuotationVersion
    ) -> dict[str, object]:
        return {
            "selection_id": str(record.selection_id),
            "product_name": record.product_name,
            "store_id": record.store_id,
            "marketplace": record.marketplace,
            "supplier_name": quotation.supplier_name,
            "unit_cost": str(quotation.unit_cost) if quotation.unit_cost is not None else None,
            "currency": quotation.currency,
            "moq": quotation.moq,
            "freight_per_unit": (
                str(quotation.freight_per_unit)
                if quotation.freight_per_unit is not None
                else None
            ),
            "lead_time_days": quotation.lead_time_days,
            "value_status": quotation.value_status,
            "quotation_version": quotation.version,
            "submission_status": quotation.submission_status,
            "recorded_by": str(quotation.recorded_by),
            "quotation_created_at": quotation.created_at.isoformat(),
            "source_version": record.source_version,
        }

    @staticmethod
    def _snapshot_checksum(
        stage: SelectionExportStage,
        schema_version: str,
        filters: dict[str, str],
        store_scope: list[str],
        rows: list[dict[str, object]],
    ) -> str:
        encoded = json.dumps(
            {
                "stage": stage.value,
                "schema_version": schema_version,
                "filters": filters,
                "store_scope": store_scope,
                "rows": rows,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
