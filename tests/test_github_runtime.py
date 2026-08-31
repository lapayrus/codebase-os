import httpx

from codebase_os.providers.github import GitHubHttpClient


def test_github_http_client_exchanges_installation_token_and_lists_pages():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/app/installations/7/access_tokens"):
            return httpx.Response(201, json={"token": "installation-token"})
        return httpx.Response(200, json={"repositories": [{"full_name": "acme/demo"}]})

    client = GitHubHttpClient("app-jwt", installation_id=7, transport=httpx.MockTransport(handler))
    assert client.installation_token(7) == "installation-token"
    assert client.installation_repositories(7) == [{"full_name": "acme/demo"}]
    assert calls[0].headers["authorization"] == "Bearer app-jwt"
    assert calls[2].headers["authorization"] == "token installation-token"


def test_github_http_client_retries_transient_response():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(502)
        if request.url.path.endswith("access_tokens"):
            return httpx.Response(201, json={"token": "installation-token"})
        return httpx.Response(200, json={"repositories": []})

    client = GitHubHttpClient("app-jwt", transport=httpx.MockTransport(handler), retries=1)
    assert client.installation_repositories(7) == []
    assert attempts == 3


def test_github_http_client_snapshot_reads_text_files():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("access_tokens"):
            return httpx.Response(201, json={"token": "installation-token"})
        if request.url.path.endswith("/repos/acme/demo"):
            return httpx.Response(200, json={"default_branch": "main"})
        if request.url.path.endswith("/git/refs/heads/main"):
            return httpx.Response(200, json={"object": {"sha": "abc"}})
        if request.url.path.endswith("/git/trees/abc"):
            return httpx.Response(
                200,
                json={"tree": [{"path": "README.md", "type": "blob", "sha": "file"}]},
            )
        return httpx.Response(200, json={"encoding": "base64", "content": "SGk="})

    client = GitHubHttpClient("app-jwt", installation_id=7, transport=httpx.MockTransport(handler))
    snapshot = client.repository_snapshot("acme/demo", "main")
    assert snapshot.name == "acme/demo"
    assert snapshot.commit == "abc"
    assert snapshot.files == {"README.md": "Hi"}
