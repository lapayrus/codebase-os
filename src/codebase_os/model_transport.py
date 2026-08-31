import json
from typing import Any, Protocol
from urllib.request import Request, urlopen


class JsonTransport(Protocol):
    def request(self, method: str, url: str, headers: dict[str, str], payload: dict[str, Any]) -> str: ...


class UrllibTransport:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def request(self, method: str, url: str, headers: dict[str, str], payload: dict[str, Any]) -> str:
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method=method)
        with urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8")
