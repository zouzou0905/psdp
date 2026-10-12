import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "access_token",
        "refresh_token",
        "token",
        "api_key",
        "authorization",
        "cookie",
        "secret",
        "database_url",
        "connection_string",
        "prompt",
        "full_prompt",
        "messages",
        "system_prompt",
        "user_prompt",
    }
)
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)bearer\s+[a-z0-9._~+\-/]+=*"),
    re.compile(r"(?i)(?:postgres(?:ql)?|mysql|mongodb)(?:\+\w+)?://[^\s]+"),
    re.compile(r"(?i)(password|api[_-]?key|secret|token)\s*[=:]\s*[^\s,;]+"),
)


class RedactionService:
    def redact_text(self, value: str) -> str:
        result = value
        for pattern in SENSITIVE_PATTERNS:
            result = pattern.sub(REDACTED, result)
        return result

    def redact(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.redact_text(value)
        if isinstance(value, Mapping):
            return {
                str(key): REDACTED if str(key).lower() in SENSITIVE_KEYS else self.redact(item)
                for key, item in value.items()
            }
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
            return [self.redact(item) for item in value]
        return value
