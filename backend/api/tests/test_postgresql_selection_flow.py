import os
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, func, select, update

from app.core.config import Settings
from app.db.models import (
    IdentityUser,
    IdentityUserStoreScope,
    SelectionListingDraftVersion,
    SelectionProfitReviewVersion,
    SelectionRecord,
)
from app.main import create_app

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRESQL_INTEGRATION_TESTS") != "1",
    reason="Set RUN_POSTGRESQL_INTEGRATION_TESTS=1 to exercise PostgreSQL",
)


async def _login(client: httpx.AsyncClient, username: str, password: str) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    response.raise_for_status()


async def test_postgresql_selection_versions_persist_across_restart() -> None:
    settings = Settings()
    assert settings.demo_operations_password is not None
    assert settings.demo_admin_password is not None
    selection_id = uuid4()
    apps = []
    setup_app = create_app(settings)
    apps.append(setup_app)
    async with setup_app.state.session_factory() as session:
        store_id = await session.scalar(
            select(IdentityUserStoreScope.store_id)
            .join(IdentityUser, IdentityUser.user_id == IdentityUserStoreScope.user_id)
            .where(IdentityUser.username == "operations_demo")
            .limit(1)
        )
    assert store_id is not None
    try:
        async with setup_app.state.session_factory.begin() as session:
            session.add(
                SelectionRecord(
                    selection_id=selection_id,
                    store_id=store_id,
                    marketplace="integration-test",
                    product_name="PostgreSQL selection persistence test",
                    source_type="integration_test",
                    source_ref="task://not-executed",
                    source_snapshot_ref="snapshot://integration-test",
                    source_version="test-v1",
                    stage="sourced",
                    revision=1,
                )
            )

        first_app = create_app(settings)
        apps.append(first_app)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=first_app), base_url="http://test"
        ) as admin:
            await _login(admin, "admin_demo", settings.demo_admin_password.get_secret_value())
            quote = await admin.put(
                f"/api/v1/selection-records/{selection_id}/quotation",
                json={
                    "supplier_name": "Integration supplier",
                    "unit_cost": "10.0000",
                    "currency": "USD",
                    "value_status": "confirmed",
                    "moq": 10,
                    "lead_time_days": 14,
                    "freight_per_unit": None,
                    "other_cost_per_unit": None,
                    "target_price": None,
                    "notes": None,
                    "expected_revision": 1,
                },
            )
            quote.raise_for_status()

        async with setup_app.state.session_factory.begin() as session:
            session.add(
                SelectionProfitReviewVersion(
                    selection_id=selection_id,
                    version=1,
                    quotation_version=1,
                    margin_amount=None,
                    margin_rate=None,
                    currency="USD",
                    value_status="missing",
                    recommendation="needs_data",
                    explanation="No formula configured; no profit conclusion produced.",
                    missing_inputs=["profit_formula"],
                    task_id="tsk_pg_boundary_only",
                    run_id=None,
                )
            )
            await session.execute(
                update(SelectionRecord)
                .where(SelectionRecord.selection_id == selection_id)
                .values(stage="profit_reviewed")
            )

        second_app = create_app(settings)
        apps.append(second_app)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=second_app), base_url="http://test"
        ) as operations:
            await _login(
                operations,
                "operations_demo",
                settings.demo_operations_password.get_secret_value(),
            )
            record = await operations.get(f"/api/v1/selection-records/{selection_id}")
            record.raise_for_status()
            revision = record.json()["revision"]
            final = await operations.put(
                f"/api/v1/selection-records/{selection_id}/final-selection",
                json={
                    "decision": "selected",
                    "reason": "Integration test decision",
                    "expected_revision": revision,
                },
            )
            final.raise_for_status()
            competitors = [
                {"title": f"Competitor {index}", "bullets": [f"Point {n}" for n in range(5)]}
                for index in range(3)
            ]
            saved = await operations.put(
                f"/api/v1/selection-records/{selection_id}/competitors",
                json={"competitors": competitors, "expected_revision": revision + 1},
            )
            saved.raise_for_status()

        async with setup_app.state.session_factory.begin() as session:
            session.add_all(
                [
                    SelectionListingDraftVersion(
                        selection_id=selection_id,
                        version=version,
                        final_version=2,
                        title=f"Persisted Listing title v{version}",
                        bullets=[f"Bullet {index}" for index in range(1, 6)],
                        status="draft",
                        task_id=f"tsk_pg_listing_{version}",
                        run_id=f"run_pg_listing_{version}",
                    )
                    for version in (1, 2)
                ]
            )

        third_app = create_app(settings)
        apps.append(third_app)
        transport = httpx.ASGITransport(app=third_app)
        async with (
            httpx.AsyncClient(transport=transport, base_url="http://test") as admin,
            httpx.AsyncClient(transport=transport, base_url="http://test") as operations,
        ):
            await _login(admin, "admin_demo", settings.demo_admin_password.get_secret_value())
            await _login(
                operations,
                "operations_demo",
                settings.demo_operations_password.get_secret_value(),
            )
            persisted = await admin.get(f"/api/v1/selection-records/{selection_id}")
            persisted.raise_for_status()
            assert persisted.json()["stage"] == "final_selected"
            assert (
                await admin.get(
                    f"/api/v1/selection-records/{selection_id}/competitors"
                )
            ).status_code == 403
            saved_competitors = await operations.get(
                f"/api/v1/selection-records/{selection_id}/competitors"
            )
            saved_competitors.raise_for_status()
            assert len(saved_competitors.json()["competitors"]) == 3
            assert (
                await admin.get(f"/api/v1/selection-records/{selection_id}/listing-draft")
            ).status_code == 403
            listing = await operations.get(
                f"/api/v1/selection-records/{selection_id}/listing-draft"
            )
            listing.raise_for_status()
            assert listing.json()["version"] == 2
        async with setup_app.state.session_factory() as session:
            history_count = await session.scalar(
                select(func.count())
                .select_from(SelectionListingDraftVersion)
                .where(SelectionListingDraftVersion.selection_id == selection_id)
            )
        assert history_count == 2
    finally:
        async with setup_app.state.session_factory.begin() as session:
            await session.execute(
                delete(SelectionRecord).where(SelectionRecord.selection_id == selection_id)
            )
        for app in apps:
            await app.state.engine.dispose()
