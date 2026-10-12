from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import session_scope


async def test_session_scope_creates_independent_sessions(app: object) -> None:
    session_factory = app.state.session_factory  # type: ignore[attr-defined]

    first: AsyncSession | None = None
    async for session in session_scope(session_factory):
        first = session

    second: AsyncSession | None = None
    async for session in session_scope(session_factory):
        second = session

    assert first is not None
    assert second is not None
    assert first is not second
