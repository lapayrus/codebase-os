from codebase_os.providers.github import GitHubProvider


class FakeGitHub:
    def installation_token(self, installation_id):
        return f"token-{installation_id}"

    def installation_repositories(self, installation_id):
        return [
            {"full_name": "acme/z", "permissions": {"contents": "read"}},
            {"full_name": "acme/a", "permissions": {"contents": "read", "metadata": "read"}},
        ]


def test_installation_snapshot_is_sorted_and_scoped():
    result = GitHubProvider(FakeGitHub()).installation(42)
    assert result.installation_id == 42
    assert result.repositories == ("acme/a", "acme/z")
    assert result.source_permissions == (
        "acme/a:contents=read,metadata=read",
        "acme/z:contents=read",
    )


def test_installation_token_is_acquired_through_client():
    assert GitHubProvider(FakeGitHub()).installation_token(42) == "token-42"
