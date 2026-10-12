from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import session_scope


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Request-scoped session dependency for database-backed application services."""

    async for session in session_scope(request.app.state.session_factory):
        yield session
