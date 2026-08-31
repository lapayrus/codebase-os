# CodebaseOS

Evidence-first repository intelligence for engineering teams.

This first vertical slice indexes a local repository, extracts symbols and imports, retrieves compact lexical and structural evidence, preserves human memories, and exposes answers with commit-pinned citations. It is intentionally read-only and model-free by default so trust and retrieval behavior can be evaluated before adding an LLM gateway.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn codebase_os.main:app --reload
```

The supported project workflow uses `uv`:

```powershell
uv sync --locked --extra dev
uv run pytest -q
uv run uvicorn codebase_os.main:app --reload --env-file .env
```

Copy `.env.example` to `.env` and fill in provider credentials before enabling integrations.
Never commit `.env` or paste private keys and API secrets into source control.

Open `http://127.0.0.1:8000`, then index a repository:

```powershell
Invoke-RestMethod -Method Post 'http://127.0.0.1:8000/api/repositories/index?path=C:\path\to\repo&name=my-repo'
```

Query through the UI or API:

```powershell
Invoke-RestMethod -Method Post 'http://127.0.0.1:8000/api/query' -ContentType 'application/json' -Body '{"question":"Where is authentication implemented?","repository":"my-repo"}'
```

## Next production increments

- Replace local directory ingestion with a GitHub App and webhook-driven incremental indexing.
- Add durable PostgreSQL/object storage persistence and tenant-aware authorization.
- Add a model gateway that drafts structured claims, while the evidence validator remains deterministic.
- Add semantic retrieval and cross-repository relationship modeling.
- Build the benchmark around citation correctness, abstention, freshness, latency, and token cost.
