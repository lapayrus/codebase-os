from dataclasses import dataclass
from fastapi import Request
import jwt

from .config import Settings


@dataclass(frozen=True)
class AuthContext:
    tenant_id: str
    user_id: str
    repositories: frozenset[str]


def context_from_request(request: Request, settings: Settings | None = None) -> AuthContext:
    if settings is not None and settings.environment == "production":
        authorization = request.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer ") or settings.supabase_jwt_secret is None:
            raise PermissionError("valid session required")
        try:
            claims = jwt.decode(
                authorization[7:],
                settings.supabase_jwt_secret.get_secret_value(),
                algorithms=["HS256"],
                options={"require": ["sub", "exp"]},
            )
        except jwt.PyJWTError as exc:
            raise PermissionError("valid session required") from exc
        metadata = claims.get("app_metadata") or {}
        repositories = frozenset(claims.get("repositories") or metadata.get("repositories") or ())
        return AuthContext(claims.get("tenant_id") or metadata.get("tenant_id") or "", claims["sub"], repositories)
    repositories = frozenset(filter(None, request.headers.get("x-repository-access", "").split(",")))
    return AuthContext(request.headers.get("x-tenant-id", "local"), request.headers.get("x-user-id", "local"), repositories)


def can_access(context: AuthContext, repository: str) -> bool:
    return not context.repositories or repository in context.repositories
