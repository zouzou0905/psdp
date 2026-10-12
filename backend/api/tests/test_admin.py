import httpx

from app.modules.audit.repository import InMemoryAuditRepository
from app.modules.identity.domain import RoleName


async def test_admin_sensitive_read_is_redacted_and_audited(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
    audit_repository: InMemoryAuditRepository,
) -> None:
    response = await client.get("/api/v1/admin/errors", headers=auth_headers[RoleName.ADMIN])

    assert response.status_code == 200
    serialized = response.text.lower()
    assert "password@" not in serialized
    assert "secret-token" not in serialized
    assert "[redacted]" in serialized
    assert any(event.action == "admin.error.read" for event in audit_repository.events)


async def test_admin_can_read_feedback_and_append_only_audit(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    feedback = await client.get("/api/v1/admin/ai-feedback", headers=auth_headers[RoleName.ADMIN])
    audit = await client.get("/api/v1/admin/audit-logs", headers=auth_headers[RoleName.ADMIN])

    assert feedback.status_code == 200
    assert feedback.json()["total"] == 1
    assert audit.status_code == 200
    assert audit.json()["total"] >= 1


async def test_logout_invalidates_existing_token(client: httpx.AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "operations_demo", "password": "valid-test-password"},
    )
    session_cookie = login.cookies.get("ai_ops_session")
    assert session_cookie is not None
    headers = {"Cookie": f"ai_ops_session={session_cookie}"}

    logout = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 204
    assert 'ai_ops_session=""' in logout.headers["set-cookie"]
    assert (await client.get("/api/v1/me", headers=headers)).status_code == 401


async def test_failed_login_and_permission_denial_are_audited(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
    audit_repository: InMemoryAuditRepository,
) -> None:
    failed_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "operations_demo", "password": "wrong-password"},
    )
    denied = await client.get("/api/v1/admin/errors", headers=auth_headers[RoleName.OPERATIONS])

    assert failed_login.status_code == 401
    assert denied.status_code == 403
    assert any(
        event.action == "identity.login" and event.result == "failure"
        for event in audit_repository.events
    )
    assert any(
        event.action == "authorization.denied" and event.result == "denied"
        for event in audit_repository.events
    )


async def test_validation_error_does_not_echo_sensitive_input(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "operations_demo", "password": {"token": "do-not-leak"}},
    )

    assert response.status_code == 422
    assert "do-not-leak" not in response.text
