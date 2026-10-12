from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class StoreStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Store(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    store_id: str
    display_name: str
    marketplace: str
    organization_id: str
    status: StoreStatus
    credential_ref: str | None
    revision: int
    created_at: datetime
    updated_at: datetime


class StoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_id: str
    display_name: str
    marketplace: str
    organization_id: str
    status: StoreStatus
    credential_configured: bool
    revision: int
    created_at: datetime
    updated_at: datetime


class StoreListResponse(BaseModel):
    items: list[StoreResponse]
    total: int = Field(ge=0)


class CreateStoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,63}$")
    display_name: str = Field(min_length=1, max_length=160)
    marketplace: str = Field(min_length=1, max_length=80)
    organization_id: str = Field(min_length=1, max_length=120)


class UpdateStoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    marketplace: str | None = Field(default=None, min_length=1, max_length=80)
    organization_id: str | None = Field(default=None, min_length=1, max_length=120)
    status: StoreStatus | None = None
    expected_revision: int = Field(ge=1)


def to_store_response(store: Store) -> StoreResponse:
    return StoreResponse(
        store_id=store.store_id,
        display_name=store.display_name,
        marketplace=store.marketplace,
        organization_id=store.organization_id,
        status=store.status,
        credential_configured=store.credential_ref is not None,
        revision=store.revision,
        created_at=store.created_at,
        updated_at=store.updated_at,
    )
