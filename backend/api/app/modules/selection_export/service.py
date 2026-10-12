import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from app.core.errors import ApplicationError
from app.db.models import SelectionExportJob
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import ModuleCode, Permission, Principal
from app.modules.selection_export.domain import (
    DownloadableExport,
    SelectionExportCreateRequest,
    SelectionExportResponse,
    SelectionExportStage,
    SelectionExportStatus,
)
from app.modules.selection_export.exporter import StageExporter
from app.modules.selection_export.repository import SelectionExportRepository


class SelectionExportService:
    def __init__(
        self,
        repository: SelectionExportRepository,
        audit_service: AuditService,
        exporters: dict[SelectionExportStage, StageExporter],
        storage_path: Path,
        file_ttl_hours: int,
    ) -> None:
        self._repository = repository
        self._audit_service = audit_service
        self._exporters = exporters
        self._storage_path = storage_path.resolve()
        self._file_ttl = timedelta(hours=file_ttl_hours)

    async def create(
        self,
        principal: Principal,
        payload: SelectionExportCreateRequest,
        trace_id: str | None,
    ) -> SelectionExportResponse:
        self._ensure_stage_authorized(principal, payload.stage)
        exporter = self._exporters.get(payload.stage)
        if exporter is None:
            raise ApplicationError(
                "EXPORT_STAGE_NOT_SUPPORTED",
                "The requested export stage is not implemented",
                422,
            )
        effective_store_ids = await self._effective_store_scope(
            principal, payload.store_ids
        )
        now = datetime.now(UTC)
        job = await self._repository.create_job_with_snapshot(
            requested_by=principal.user_id,
            authorization_revision=principal.authorization_revision,
            payload=payload,
            effective_store_ids=effective_store_ids,
            schema_version=exporter.schema_version,
            trace_id=trace_id,
            expires_at=now + self._file_ttl,
        )
        await self._audit(
            principal,
            "selection.export.create",
            job,
            AuditResult.SUCCESS,
            {
                "stage": job.stage,
                "snapshot_id": str(job.snapshot_id),
                "store_scope": json.dumps(job.store_scope_json, sort_keys=True),
                "filters": json.dumps(job.filters_json, sort_keys=True),
            },
        )
        return await self._generate(principal, job, exporter)

    async def get(self, principal: Principal, export_id: UUID) -> SelectionExportResponse:
        job = await self._owned_job(principal, export_id)
        self._ensure_stage_authorized(principal, SelectionExportStage(job.stage))
        await self._ensure_job_scope(principal, job)
        return SelectionExportResponse.model_validate(job)

    async def download(self, principal: Principal, export_id: UUID) -> DownloadableExport:
        job = await self._owned_job(principal, export_id)
        self._ensure_stage_authorized(principal, SelectionExportStage(job.stage))
        await self._ensure_job_scope(principal, job)
        if job.status != SelectionExportStatus.COMPLETED.value:
            raise ApplicationError(
                "EXPORT_NOT_READY", "The export file is not available", 409
            )
        if self._as_utc(job.expires_at) <= datetime.now(UTC):
            raise ApplicationError("EXPORT_FILE_EXPIRED", "The export file has expired", 410)
        if not job.file_path or not job.file_name or not job.file_checksum:
            raise ApplicationError("EXPORT_FILE_MISSING", "The export file is unavailable", 410)
        path, exists = await asyncio.to_thread(self._resolve_export_path, job.file_path)
        if path.parent != self._storage_path or not exists:
            raise ApplicationError("EXPORT_FILE_MISSING", "The export file is unavailable", 410)
        checksum = await asyncio.to_thread(self._checksum, path)
        if checksum != job.file_checksum:
            raise ApplicationError(
                "EXPORT_FILE_INTEGRITY_FAILED", "The export file failed integrity validation", 409
            )
        await self._audit(
            principal,
            "selection.export.download",
            job,
            AuditResult.SUCCESS,
            {"file_checksum": checksum},
        )
        return DownloadableExport(path=path, file_name=job.file_name, checksum=checksum)

    async def _generate(
        self,
        principal: Principal,
        job: SelectionExportJob,
        exporter: StageExporter,
    ) -> SelectionExportResponse:
        # This is the worker boundary. A future queue consumer must rebuild the same
        # principal and repeat these checks before calling the exporter.
        self._ensure_stage_authorized(principal, SelectionExportStage(job.stage))
        await self._ensure_job_scope(principal, job)
        await self._repository.mark_running(job.export_id)
        snapshot = await self._repository.get_snapshot(job.snapshot_id)
        if snapshot is None or snapshot.requested_by != principal.user_id:
            await self._repository.mark_failed(
                job.export_id, "EXPORT_SNAPSHOT_MISSING", "Frozen snapshot is unavailable"
            )
            return await self.get(principal, job.export_id)
        try:
            store_names = await self._repository.store_display_names(snapshot.store_scope)
            generated = await asyncio.to_thread(
                exporter.export,
                snapshot,
                requested_by=principal.user_id,
                requested_at=self._as_utc(job.created_at),
                store_names=store_names,
                output_directory=self._storage_path,
            )
            await self._repository.mark_completed(job.export_id, generated)
        except Exception:
            await self._repository.mark_failed(
                job.export_id,
                "EXPORT_GENERATION_FAILED",
                "Spreadsheet generation failed; inspect protected server logs",
            )
            failed = await self._owned_job(principal, job.export_id)
            await self._audit(
                principal,
                "selection.export.generate",
                failed,
                AuditResult.FAILURE,
                {"error_code": "EXPORT_GENERATION_FAILED"},
            )
            return SelectionExportResponse.model_validate(failed)
        completed = await self._owned_job(principal, job.export_id)
        await self._audit(
            principal,
            "selection.export.generate",
            completed,
            AuditResult.SUCCESS,
            {
                "row_count": str(completed.row_count),
                "file_checksum": completed.file_checksum or "",
            },
        )
        return SelectionExportResponse.model_validate(completed)

    async def _owned_job(
        self, principal: Principal, export_id: UUID
    ) -> SelectionExportJob:
        job = await self._repository.get_owned_job(export_id, principal.user_id)
        if job is None:
            raise ApplicationError("EXPORT_NOT_FOUND", "Selection export not found", 404)
        return job

    @staticmethod
    def _ensure_stage_authorized(
        principal: Principal, stage: SelectionExportStage
    ) -> None:
        requirements = {
            SelectionExportStage.INITIAL_SELECTION: (
                Permission.SELECTION_EXPORT,
                {ModuleCode.OPERATIONS, ModuleCode.PROCUREMENT, ModuleCode.ADMIN},
            ),
            SelectionExportStage.QUOTATION: (
                Permission.QUOTATION_EXPORT,
                {ModuleCode.PROCUREMENT, ModuleCode.ADMIN},
            ),
        }
        permission, allowed_modules = requirements[stage]
        if permission not in principal.permissions or principal.modules.isdisjoint(
            allowed_modules
        ):
            raise ApplicationError("PERMISSION_DENIED", "Permission denied", 403)

    async def _effective_store_scope(
        self, principal: Principal, requested_store_ids: list[str]
    ) -> list[str] | None:
        if Permission.ALL_BUSINESS_READ in principal.permissions:
            return sorted(requested_store_ids) if requested_store_ids else None
        authorized = await self._repository.authorized_store_ids(
            set(principal.scope.store_ids), set(principal.scope.organization_ids)
        )
        requested = set(requested_store_ids)
        if requested and not requested.issubset(authorized):
            raise ApplicationError(
                "STORE_SCOPE_DENIED", "Store is outside the authorized scope", 403
            )
        return sorted(requested or authorized)

    async def _ensure_job_scope(
        self, principal: Principal, job: SelectionExportJob
    ) -> None:
        if Permission.ALL_BUSINESS_READ in principal.permissions:
            return
        authorized = await self._repository.authorized_store_ids(
            set(principal.scope.store_ids), set(principal.scope.organization_ids)
        )
        if not set(job.store_scope_json).issubset(authorized):
            raise ApplicationError(
                "STORE_SCOPE_DENIED", "Export is outside the authorized store scope", 403
            )

    async def _audit(
        self,
        principal: Principal,
        action: str,
        job: SelectionExportJob,
        result: AuditResult,
        metadata: dict[str, str],
    ) -> None:
        await self._audit_service.record(
            action=action,
            resource_type="selection_export",
            resource_id=str(job.export_id),
            result=result,
            trace_id=job.trace_id,
            principal=principal,
            metadata_summary=metadata,
        )

    @staticmethod
    def _checksum(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _resolve_export_path(raw_path: str) -> tuple[Path, bool]:
        path = Path(raw_path).resolve()
        return path, path.is_file()

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
