from datetime import datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SelectionExportStage(StrEnum):
    INITIAL_SELECTION = "initial_selection"
    QUOTATION = "quotation"


class SelectionExportStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SelectionExportCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: SelectionExportStage
    store_ids: list[str] = Field(default_factory=list, max_length=100)
    search: str | None = Field(default=None, max_length=200)
    marketplace: str | None = Field(default=None, max_length=80)
    source_type: str | None = Field(default=None, max_length=40)

    @field_validator("store_ids")
    @classmethod
    def unique_store_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("store_ids cannot contain empty values")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("store_ids cannot contain duplicates")
        return cleaned

    @field_validator("search", "marketplace", "source_type")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    def filters(self) -> dict[str, str]:
        return {
            key: value
            for key, value in {
                "search": self.search,
                "marketplace": self.marketplace,
                "source_type": self.source_type,
            }.items()
            if value is not None
        }


class SelectionExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    export_id: UUID
    stage: SelectionExportStage
    snapshot_id: UUID
    schema_version: str
    status: SelectionExportStatus
    row_count: int = Field(ge=0)
    file_name: str | None
    file_checksum: str | None
    error_code: str | None
    trace_id: str | None
    created_at: datetime
    completed_at: datetime | None
    expires_at: datetime


class FrozenSnapshotRow(BaseModel):
    row_position: int = Field(ge=1)
    selection_id: UUID
    selection_revision: int = Field(ge=1)
    rendered_row: dict[str, object]


class FrozenSnapshot(BaseModel):
    snapshot_id: UUID
    stage: SelectionExportStage
    schema_version: str
    filters: dict[str, object]
    store_scope: list[str]
    requested_by: UUID
    row_count: int
    snapshot_checksum: str
    created_at: datetime
    rows: list[FrozenSnapshotRow]


class GeneratedExportFile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    file_name: str
    checksum: str


class DownloadableExport(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    file_name: str
    checksum: str
