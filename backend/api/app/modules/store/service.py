import json
from datetime import UTC, datetime

from app.core.errors import ApplicationError
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import Permission, Principal
from app.modules.store.domain import (
    CreateStoreRequest,
    Store,
    StoreListResponse,
    StoreResponse,
    StoreStatus,
    UpdateStoreRequest,
    to_store_response,
)
from app.modules.store.repository import StoreRepository, StoreRevisionConflictError


class StoreService:
    def __init__(self, repository: StoreRepository, audit_service: AuditService) -> None:
        self._repository = repository
        self._audit_service = audit_service

    async def list_for_user(self, principal: Principal) -> StoreListResponse:
        if Permission.ALL_BUSINESS_READ in principal.permissions:
            stores = await self._repository.list_all()
        else:
            stores = await self._repository.list_by_ids(principal.scope.store_ids)
        return StoreListResponse(
            items=[to_store_response(store) for store in stores], total=len(stores)
        )

    async def list_all(self) -> StoreListResponse:
        stores = await self._repository.list_all()
        return StoreListResponse(
            items=[to_store_response(store) for store in stores], total=len(stores)
        )

    async def create(
        self, principal: Principal, payload: CreateStoreRequest, trace_id: str | None
    ) -> StoreResponse:
        now = datetime.now(UTC)
        store = Store(
            store_id=payload.store_id,
            display_name=payload.display_name,
            marketplace=payload.marketplace,
            organization_id=payload.organization_id,
            status=StoreStatus.ACTIVE,
            credential_ref=None,
            revision=1,
            created_at=now,
            updated_at=now,
        )
        try:
            created = await self._repository.create(store)
        except ValueError as exc:
            raise ApplicationError("STORE_ALREADY_EXISTS", "Store already exists", 409) from exc
        await self._audit_store_change(
            principal, "store.create", created.store_id, None, created, trace_id
        )
        return to_store_response(created)

    async def update(
        self,
        principal: Principal,
        store_id: str,
        payload: UpdateStoreRequest,
        trace_id: str | None,
    ) -> StoreResponse:
        before = await self._repository.get(store_id)
        if before is None:
            raise ApplicationError("STORE_NOT_FOUND", "Store not found", 404)
        updated_values = payload.model_dump(exclude={"expected_revision"}, exclude_none=True)
        candidate = before.model_copy(update=updated_values)
        try:
            after = await self._repository.update(candidate, payload.expected_revision)
        except StoreRevisionConflictError as exc:
            raise ApplicationError(
                "STORE_REVISION_CONFLICT", "Store changed; reload before updating", 409
            ) from exc
        await self._audit_store_change(principal, "store.update", store_id, before, after, trace_id)
        return to_store_response(after)

    async def _audit_store_change(
        self,
        principal: Principal,
        action: str,
        store_id: str,
        before: Store | None,
        after: Store,
        trace_id: str | None,
    ) -> None:
        await self._audit_service.record(
            action=action,
            resource_type="store",
            resource_id=store_id,
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=principal,
            metadata_summary={
                "before": json.dumps(
                    to_store_response(before).model_dump(mode="json") if before else None,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "after": json.dumps(
                    to_store_response(after).model_dump(mode="json"),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            },
        )
