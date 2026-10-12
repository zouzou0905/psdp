from dataclasses import dataclass

from app.db.health import DatabaseHealthProbe


@dataclass(frozen=True, slots=True)
class Readiness:
    healthy: bool
    database: str


class HealthService:
    def __init__(self, database_probe: DatabaseHealthProbe) -> None:
        self._database_probe = database_probe

    async def readiness(self) -> Readiness:
        ready = await self._database_probe.is_ready()
        return Readiness(healthy=ready, database="up" if ready else "down")
