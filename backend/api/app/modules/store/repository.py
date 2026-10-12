from datetime import UTC, datetime
from typing import Any, Protocol, cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import StoreRecord
from app.modules.store.domain import Store, StoreStatus


class StoreRevisionConflictError(Exception):
    pass


class StoreRepository(Protocol):
    async def list_all(self) -> list[Store]: ...

    async def list_by_ids(self, store_ids: frozenset[str]) -> list[Store]: ...

    async def get(self, store_id: str) -> Store | None: ...

    async def create(self, store: Store) -> Store: ...

    async def update(self, store: Store, expected_revision: int) -> Store: ...


class InMemoryStoreRepository:
    def __init__(self, stores: list[Store] | None = None) -> None:
        self._stores = {store.store_id: store for store in stores or []}

    async def list_all(self) -> list[Store]:
        return sorted(self._stores.values(), key=lambda item: item.store_id)

    async def list_by_ids(self, store_ids: frozenset[str]) -> list[Store]:
        return sorted(
            (store for store_id, store in self._stores.items() if store_id in store_ids),
            key=lambda item: item.store_id,
        )

    async def get(self, store_id: str) -> Store | None:
        return self._stores.get(store_id)

    async def create(self, store: Store) -> Store:
        if store.store_id in self._stores:
            raise ValueError("store_exists")
        self._stores[store.store_id] = store
        return store

    async def update(self, store: Store, expected_revision: int) -> Store:
        current = self._stores.get(store.store_id)
        if current is None:
            raise KeyError(store.store_id)
        if current.revision != expected_revision:
            raise StoreRevisionConflictError
        updated = store.model_copy(
            update={"revision": current.revision + 1, "updated_at": datetime.now(UTC)}
        )
        self._stores[store.store_id] = updated
        return updated


class SqlAlchemyStoreRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_all(self) -> list[Store]:
        async with self._session_factory() as session:
            rows = (await session.scalars(select(StoreRecord).order_by(StoreRecord.store_id))).all()
        return [self._to_domain(row) for row in rows]

    async def list_by_ids(self, store_ids: frozenset[str]) -> list[Store]:
        if not store_ids:
            return []
        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(StoreRecord)
                    .where(StoreRecord.store_id.in_(store_ids))
                    .order_by(StoreRecord.store_id)
                )
            ).all()
        return [self._to_domain(row) for row in rows]

    async def get(self, store_id: str) -> Store | None:
        async with self._session_factory() as session:
            row = await session.get(StoreRecord, store_id)
        return self._to_domain(row) if row else None

    async def create(self, store: Store) -> Store:
        async with self._session_factory.begin() as session:
            if await session.get(StoreRecord, store.store_id) is not None:
                raise ValueError("store_exists")
            session.add(
                StoreRecord(
                    store_id=store.store_id,
                    display_name=store.display_name,
                    marketplace=store.marketplace,
                    organization_id=store.organization_id,
                    status=store.status.value,
                    credential_ref=store.credential_ref,
                    revision=store.revision,
                    created_at=store.created_at,
                    updated_at=store.updated_at,
                )
            )
        return store

    async def update(self, store: Store, expected_revision: int) -> Store:
        now = datetime.now(UTC)
        async with self._session_factory.begin() as session:
            result = await session.execute(
                update(StoreRecord)
                .where(
                    StoreRecord.store_id == store.store_id,
                    StoreRecord.revision == expected_revision,
                )
                .values(
                    display_name=store.display_name,
                    marketplace=store.marketplace,
                    organization_id=store.organization_id,
                    status=store.status.value,
                    revision=expected_revision + 1,
                    updated_at=now,
                )
            )
            if cast(CursorResult[Any], result).rowcount != 1:
                raise StoreRevisionConflictError
        return store.model_copy(update={"revision": expected_revision + 1, "updated_at": now})

    @staticmethod
    def _to_domain(row: StoreRecord) -> Store:
        return Store(
            store_id=row.store_id,
            display_name=row.display_name,
            marketplace=row.marketplace,
            organization_id=row.organization_id,
            status=StoreStatus(row.status),
            credential_ref=row.credential_ref,
            revision=row.revision,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
