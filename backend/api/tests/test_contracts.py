import json
from pathlib import Path

import httpx


async def test_openapi_contains_required_routes(client: httpx.AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health/live" in paths
    assert "/health/ready" in paths
    assert "/api/v1/system/info" in paths
    assert "/api/v1/dashboard/summary" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/me" in paths
    assert "/api/v1/me/access-context" in paths
    assert "/api/v1/me/modules" in paths
    assert "/api/v1/me/stores" in paths
    assert "/api/v1/operations/dashboard" in paths
    assert "/api/v1/procurement/dashboard" in paths
    assert "/api/v1/creative/dashboard" in paths
    assert "/api/v1/admin/dashboard" in paths
    assert "/api/v1/admin/users" in paths
    assert "post" in paths["/api/v1/admin/users"]
    assert "/api/v1/admin/users/{user_id}/enable" in paths
    assert "/api/v1/admin/users/{user_id}/disable" in paths
    assert "/api/v1/admin/users/{user_id}/roles" in paths
    assert "/api/v1/admin/users/{user_id}/modules" in paths
    assert "/api/v1/admin/users/{user_id}/store-scopes" in paths
    assert "/api/v1/admin/stores" in paths
    assert "/api/v1/admin/stores/{store_id}" in paths
    assert "/api/v1/admin/errors" in paths
    assert "/api/v1/admin/ai-feedback" in paths
    assert "/api/v1/admin/audit-logs" in paths
    assert "/api/v1/admin/capabilities/deepseek/status" in paths
    assert "/api/v1/selection-records" in paths
    assert "/api/v1/selection-records/{selection_id}/quotation" in paths
    assert "/api/v1/selection-records/{selection_id}/profit-review" in paths
    assert "/api/v1/selection-records/{selection_id}/final-selection" in paths
    assert "/api/v1/selection-records/{selection_id}/competitors" in paths
    assert "/api/v1/selection-records/{selection_id}/ai-tasks" in paths
    assert "/api/v1/selection-records/{selection_id}/listing-draft" in paths
    assert "/api/v1/selection-exports" in paths
    assert "/api/v1/selection-exports/{export_id}" in paths
    assert "/api/v1/selection-exports/{export_id}/download" in paths
    assert "/api/v1/selection-skills" in paths
    assert "/api/v1/selection-skills/{skill_key}" in paths
    login_schema = paths["/api/v1/auth/login"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert login_schema["$ref"] == "#/components/schemas/AccessContextResponse"
    cookie_scheme = response.json()["components"]["securitySchemes"]["APIKeyCookie"]
    assert cookie_scheme == {"type": "apiKey", "in": "cookie", "name": "ai_ops_session"}
    schemas = response.json()["components"]["schemas"]
    assert schemas["SelectionExportStage"]["enum"] == [
        "initial_selection",
        "quotation",
    ]
    assert "quotation.export" in schemas["Permission"]["enum"]


def test_shared_contract_artifacts_exist() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    contracts = repository_root / "shared" / "contracts"

    assert (contracts / "openapi.v1.json").is_file()
    for name in (
        "dashboard-summary.example.json",
        "dashboard-summary.schema.json",
        "current-user.example.json",
        "login.example.json",
        "access-context.example.json",
        "modules.example.json",
        "stores.example.json",
        "admin-user-access.example.json",
        "admin-users.example.json",
        "admin-access-updates.example.json",
        "admin-user-create.example.json",
        "admin-user-status.example.json",
        "permission-error.example.json",
        "admin-errors.example.json",
        "ai-feedback.example.json",
        "audit-logs.example.json",
        "selection-flow.example.json",
        "selection-ai-task.example.json",
        "deepseek-status.example.json",
        "listing-copy-permissions.example.json",
        "selection-export.example.json",
        "selection-skills.example.json",
        "selection-candidate-output.schema.json",
    ):
        assert (contracts / name).is_file()

    login_example = json.loads((contracts / "login.example.json").read_text(encoding="utf-8"))
    assert "access_token" not in login_example["response"]
    assert login_example["session_cookie"]["http_only"] is True
