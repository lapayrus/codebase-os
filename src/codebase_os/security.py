from collections import defaultdict
from time import monotonic

from fastapi import Request


class RequestGuard:
    def __init__(self, max_request_bytes: int, rate_limit: int, window_seconds: int = 60) -> None:
        self.max_request_bytes = max_request_bytes
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check_size(self, content_length: int | None) -> str | None:
        if content_length is not None and content_length > self.max_request_bytes:
            return "request body exceeds the configured limit"
        return None

    def check_rate(self, client: str, now: float | None = None) -> str | None:
        current = monotonic() if now is None else now
        recent = [stamp for stamp in self._requests[client] if current - stamp < self.window_seconds]
        self._requests[client] = recent
        if len(recent) >= self.rate_limit:
            return "rate limit exceeded"
        recent.append(current)
        return None

    @staticmethod
    def client_key(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", maxsplit=1)[0].strip()
        return request.client.host if request.client else "unknown"
