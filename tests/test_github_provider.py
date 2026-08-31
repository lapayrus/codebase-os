from codebase_os.providers.github import GitHubProvider


class FakeGitHub:
    def installation_repositories(self, installation_id):
        return [{"full_name": "acme/z"}, {"full_name": "acme/a"}]


def test_installation_snapshot_is_sorted_and_scoped():
    result = GitHubProvider(FakeGitHub()).installation(42)
    assert result.installation_id == 42
    assert result.repositories == ("acme/a", "acme/z")

