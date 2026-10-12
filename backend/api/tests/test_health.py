import httpx

from tests.conftest import ConfigurableDatabaseProbe


async def test_liveness_and_context_headers(client: httpx.AsyncClient) -> None:
    response = await client.get(
        "/health/live",
        headers={"X-Request-ID": "req-test", "X-Trace-ID": "trace-test"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "req-test"
    assert response.headers["X-Trace-ID"] == "trace-test"


async def test_readiness_is_healthy(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "up"}}


async def test_readiness_reports_database_failure(
    client: httpx.AsyncClient,
    database_probe: ConfigurableDatabaseProbe,
) -> None:
    database_probe.ready = False

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "checks": {"database": "down"}}
