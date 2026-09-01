from pathlib import Path
import uuid


def pytest_configure(config):
    root = Path(".pytest-runs")
    root.mkdir(parents=True, exist_ok=True)
    config.option.basetemp = str(root / f"pytest-{uuid.uuid4().hex}")
