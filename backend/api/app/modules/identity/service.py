from dataclasses import dataclass
from datetime import datetime

from app.core.errors import ApplicationError
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import (
    AccessContextResponse,
    Principal,
    to_access_context,
    to_principal,
)
from app.modules.identity.repository import IdentityRepository
from app.modules.identity.security import InvalidTokenError, PasswordService, TokenService


@dataclass(frozen=True)
class LoginResult:
    session_token: str
    expires_at: datetime
    access_context: AccessContextResponse


class AuthenticationService:
    def __init__(
        self,
        repository: IdentityRepository,
        password_service: PasswordService,
        token_service: TokenService,
        audit_service: AuditService,
    ) -> None:
        self._repository = repository
        self._password_service = password_service
        self._token_service = token_service
        self._audit_service = audit_service

    async def login(self, username: str, password: str, trace_id: str | None) -> LoginResult:
        user = await self._repository.get_by_username(username)
        if (
            user is None
            or not user.is_active
            or not self._password_service.verify(password, user.password_hash)
        ):
            await self._audit_service.record(
                action="identity.login",
                resource_type="session",
                result=AuditResult.FAILURE,
                trace_id=trace_id,
                metadata_summary={"username": username, "reason": "invalid_credentials"},
            )
            raise ApplicationError(
                "INVALID_CREDENTIALS",
                "Invalid username or password",
                401,
            )

        principal = to_principal(user)
        token, expires_at = self._token_service.issue(
            user.user_id, user.token_version, user.authorization_revision
        )
        await self._audit_service.record(
            action="identity.login",
            resource_type="session",
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=principal,
        )
        return LoginResult(
            session_token=token,
            expires_at=expires_at,
            access_context=to_access_context(principal),
        )

    async def authenticate(self, token: str) -> Principal:
        try:
            claims = self._token_service.decode(token)
        except InvalidTokenError as exc:
            raise ApplicationError(
                "INVALID_TOKEN",
                "Session is invalid or expired",
                401,
            ) from exc

        user = await self._repository.get_by_id(claims.sub)
        if (
            user is None
            or not user.is_active
            or user.token_version != claims.ver
            or user.authorization_revision != claims.arev
        ):
            raise ApplicationError(
                "INVALID_TOKEN",
                "Session is invalid or expired",
                401,
            )
        return to_principal(user)

    async def logout(self, principal: Principal, trace_id: str | None) -> None:
        await self._repository.increment_token_version(principal.user_id)
        await self._audit_service.record(
            action="identity.logout",
            resource_type="session",
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=principal,
        )
