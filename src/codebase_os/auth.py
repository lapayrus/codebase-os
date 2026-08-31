from dataclasses import dataclass
from fastapi import Request


@dataclass(frozen=True)
class AuthContext:
    tenant_id: str
    user_id: str
    repositories: frozenset[str]


def context_from_request(request: Request) -> AuthContext:
    repositories = frozenset(filter(None, request.headers.get("x-repository-access", "").split(",")))
    return AuthContext(request.headers.get("x-tenant-id", "local"), request.headers.get("x-user-id", "local"), repositories)


def can_access(context: AuthContext, repository: str) -> bool:
    return not context.repositories or repository in context.repositories

