from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select, update

from app.db.base import Base
from app.db.models import (
    SelectionAiTask,
    SelectionListingDraftVersion,
    SelectionProfitReviewVersion,
    SelectionRecord,
)
from app.modules.audit.repository import InMemoryAuditRepository
from app.modules.identity.domain import Permission, RoleName
from app.modules.identity.repository import InMemoryIdentityRepository
from tests.conftest import PASSWORD, USER_IDS

SHARED_STORE = "store_shared"


@pytest.fixture
async def selection_ids(
    app: FastAPI, identity_repository: InMemoryIdentityRepository
) -> tuple[UUID, UUID]:
    for role in (RoleName.OPERATIONS, RoleName.PROCUREMENT):
        user = await identity_repository.get_by_id(USER_IDS[role])
        assert user is not None
        await identity_repository.update_store_scopes(
            user.user_id,
            frozenset({SHARED_STORE}),
            user.authorization_revision,
        )
    allowed_id = uuid4()
    denied_id = uuid4()
    async with app.state.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with app.state.session_factory.begin() as session:
        session.add_all(
            [
                SelectionRecord(
                    selection_id=allowed_id,
                    store_id=SHARED_STORE,
                    marketplace="amazon-us",
                    product_name="Shared candidate",
                    source_type="ai_skill_sorftime",
                    source_ref="task://initial-demo",
                    source_snapshot_ref="snapshot://market-demo",
                    source_version="skill-v1",
                    owner_id=USER_IDS[RoleName.OPERATIONS],
                    stage="sourced",
                    revision=1,
                ),
                SelectionRecord(
                    selection_id=denied_id,
                    store_id="store_other",
                    marketplace="amazon-ca",
                    product_name="Other store candidate",
                    source_type="import",
                    source_ref=None,
                    source_snapshot_ref="snapshot://other",
                    source_version="import-v1",
                    owner_id=None,
                    stage="sourced",
                    revision=1,
                ),
            ]
        )
        session.add_all(
            [
                SelectionListingDraftVersion(
                    selection_id=allowed_id,
                    version=version,
                    final_version=1,
                    title=f"Historical title v{version}",
                    bullets=[f"Bullet {index}" for index in range(1, 6)],
                    status="draft",
                    task_id=f"tsk_listing_{version}",
                    run_id=f"run_listing_{version}",
                )
                for version in (1, 2)
            ]
            + [
                SelectionListingDraftVersion(
                    selection_id=denied_id,
                    version=1,
                    final_version=1,
                    title="Other store sensitive title",
                    bullets=[f"Other bullet {index}" for index in range(1, 6)],
                    status="draft",
                    task_id="tsk_listing_other",
                    run_id="run_listing_other",
                ),
                SelectionAiTask(
                    task_id="tsk_listing_visible_to_operations_only",
                    selection_id=allowed_id,
                    task_type="listing_draft",
                    input_version="final:1",
                    status="succeeded",
                    run_id="run_listing_visible_to_operations_only",
                    result_version="listing:2",
                    error_code=None,
                ),
            ]
        )
    return allowed_id, denied_id


async def test_linked_selection_flow_permissions_scope_and_revision(
    app: FastAPI,
    client: httpx.AsyncClient,
    selection_ids: tuple[UUID, UUID],
    auth_headers: dict[RoleName, dict[str, str]],
    audit_repository: InMemoryAuditRepository,
    identity_repository: InMemoryIdentityRepository,
) -> None:
    selection_id, denied_id = selection_ids
    operations = auth_headers[RoleName.OPERATIONS]
    procurement = auth_headers[RoleName.PROCUREMENT]
    admin = auth_headers[RoleName.ADMIN]

    listed = await client.get("/api/v1/selection-records", headers=operations)
    assert listed.status_code == 200
    assert [item["selection_id"] for item in listed.json()["items"]] == [str(selection_id)]
    assert (
        await client.get(f"/api/v1/selection-records/{denied_id}", headers=operations)
    ).status_code == 404

    quotation_payload = {
        "supplier_name": "Supplier A",
        "unit_cost": "8.2500",
        "currency": "USD",
        "value_status": "confirmed",
        "moq": 100,
        "lead_time_days": 20,
        "freight_per_unit": "1.0000",
        "other_cost_per_unit": None,
        "target_price": "19.9900",
        "notes": "Manual procurement quotation",
        "expected_revision": 1,
    }
    quote = await client.put(
        f"/api/v1/selection-records/{selection_id}/quotation",
        headers=procurement,
        json=quotation_payload,
    )
    assert quote.status_code == 200
    assert quote.json()["version"] == 1
    assert (
        await client.get(
            f"/api/v1/selection-records/{selection_id}/quotation", headers=operations
        )
    ).status_code == 403
    stale_quote = await client.put(
        f"/api/v1/selection-records/{selection_id}/quotation",
        headers=procurement,
        json=quotation_payload,
    )
    assert stale_quote.status_code == 409

    async with app.state.session_factory.begin() as session:
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
                explanation="Formula and threshold are not configured.",
                missing_inputs=["platform_fee"],
                task_id="tsk_profit_demo",
                run_id=None,
            )
        )
        await session.execute(
            update(SelectionRecord)
            .where(SelectionRecord.selection_id == selection_id)
            .values(stage="profit_reviewed")
        )

    profit = await client.get(
        f"/api/v1/selection-records/{selection_id}/profit-review", headers=operations
    )
    assert profit.status_code == 200
    assert profit.json()["value_status"] == "missing"
    assert profit.json()["margin_amount"] is None
    assert (
        await client.get(
            f"/api/v1/selection-records/{selection_id}/profit-review", headers=procurement
        )
    ).status_code == 200

    current = await client.get(f"/api/v1/selection-records/{selection_id}", headers=operations)
    revision = current.json()["revision"]
    assert (
        await client.put(
            f"/api/v1/selection-records/{selection_id}/final-selection",
            headers=procurement,
            json={"decision": "selected", "reason": "manual", "expected_revision": revision},
        )
    ).status_code == 403
    final = await client.put(
        f"/api/v1/selection-records/{selection_id}/final-selection",
        headers=operations,
        json={"decision": "selected", "reason": "manual", "expected_revision": revision},
    )
    assert final.status_code == 200

    revision += 1
    invalid_competitors = await client.put(
        f"/api/v1/selection-records/{selection_id}/competitors",
        headers=operations,
        json={"competitors": [], "expected_revision": revision},
    )
    assert invalid_competitors.status_code == 422
    competitors = [
        {"title": f"Competitor {index}", "bullets": [f"Point {n}" for n in range(1, 6)]}
        for index in range(1, 4)
    ]
    saved = await client.put(
        f"/api/v1/selection-records/{selection_id}/competitors",
        headers=operations,
        json={"competitors": competitors, "expected_revision": revision},
    )
    assert saved.status_code == 200
    assert len(saved.json()["competitors"]) == 3
    assert all(len(item["bullets"]) == 5 for item in saved.json()["competitors"])
    assert (
        await client.get(
            f"/api/v1/selection-records/{selection_id}/competitors",
            headers=procurement,
        )
    ).status_code == 403
    assert (
        await client.put(
            f"/api/v1/selection-records/{selection_id}/competitors",
            headers=operations,
            json={"competitors": competitors, "expected_revision": revision},
        )
    ).status_code == 409

    assert (
        await client.get(
            f"/api/v1/selection-records/{selection_id}/final-selection", headers=admin
        )
    ).status_code == 200
    tasks = await client.get(
        f"/api/v1/selection-records/{selection_id}/ai-tasks", headers=procurement
    )
    assert tasks.status_code == 200
    assert tasks.json() == {"items": [], "total": 0}
    assert (
        await client.get(
            f"/api/v1/selection-records/{selection_id}/listing-draft",
            headers=procurement,
        )
    ).status_code == 403
    draft = await client.get(
        f"/api/v1/selection-records/{selection_id}/listing-draft", headers=operations
    )
    assert draft.status_code == 200
    assert draft.json()["version"] == 2
    assert draft.json()["title"] == "Historical title v2"
    assert (
        await client.get(
            f"/api/v1/selection-records/{denied_id}/listing-draft", headers=operations
        )
    ).status_code == 404
    admin_listing = await client.get(
        f"/api/v1/selection-records/{selection_id}/listing-draft", headers=admin
    )
    assert admin_listing.status_code == 403
    admin_context = await client.get("/api/v1/me/access-context", headers=admin)
    assert admin_context.status_code == 200
    assert "listing_copy.generate" not in admin_context.json()["permissions"]
    assert "listing_copy.edit" not in admin_context.json()["permissions"]
    admin_user = await identity_repository.get_by_id(USER_IDS[RoleName.ADMIN])
    assert admin_user is not None
    await identity_repository.update_roles_permissions(
        admin_user.user_id,
        admin_user.roles,
        frozenset({Permission.LISTING_COPY_READ}),
        admin_user.authorization_revision,
    )
    authorized_admin_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_demo", "password": PASSWORD},
    )
    assert authorized_admin_login.status_code == 200
    admin_cookie = authorized_admin_login.cookies.get("ai_ops_session")
    assert admin_cookie is not None
    explicitly_authorized_admin = {
        "Cookie": f"ai_ops_session={admin_cookie}"
    }
    assert (
        await client.get(
            f"/api/v1/selection-records/{selection_id}/listing-draft",
            headers=explicitly_authorized_admin,
        )
    ).status_code == 200
    operations_tasks = await client.get(
        f"/api/v1/selection-records/{selection_id}/ai-tasks", headers=operations
    )
    assert operations_tasks.status_code == 200
    assert operations_tasks.json()["items"][0]["task_type"] == "listing_draft"
    async with app.state.session_factory() as session:
        history_count = await session.scalar(
            select(func.count())
            .select_from(SelectionListingDraftVersion)
            .where(SelectionListingDraftVersion.selection_id == selection_id)
        )
    assert history_count == 2
    actions = {event.action for event in audit_repository.events}
    assert {
        "selection.quotation.save",
        "selection.final.save",
        "selection.competitors.save",
    }.issubset(actions)
