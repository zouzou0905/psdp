from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash
from pydantic import BaseModel, ValidationError


class InvalidTokenError(Exception):
    pass


class TokenClaims(BaseModel):
    sub: UUID
    ver: int
    arev: int
    jti: UUID
    iss: str
    aud: str
    iat: datetime
    exp: datetime


class PasswordService:
    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._password_hash.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return self._password_hash.verify(password, password_hash)


class TokenService:
    def __init__(self, secret: str, issuer: str, audience: str, ttl_minutes: int) -> None:
        self._secret = secret
        self._issuer = issuer
        self._audience = audience
        self._ttl = timedelta(minutes=ttl_minutes)

    def issue(
        self, user_id: UUID, token_version: int, authorization_revision: int
    ) -> tuple[str, datetime]:
        now = datetime.now(UTC)
        expires_at = now + self._ttl
        claims = {
            "sub": str(user_id),
            "ver": token_version,
            "arev": authorization_revision,
            "jti": str(uuid4()),
            "iss": self._issuer,
            "aud": self._audience,
            "iat": now,
            "exp": expires_at,
        }
        return jwt.encode(claims, self._secret, algorithm="HS256"), expires_at

    def decode(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                issuer=self._issuer,
                audience=self._audience,
                options={"require": ["sub", "ver", "arev", "jti", "iss", "aud", "iat", "exp"]},
            )
            return TokenClaims.model_validate(payload)
        except (jwt.PyJWTError, ValidationError, ValueError) as exc:
            raise InvalidTokenError from exc
