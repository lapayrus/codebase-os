from pathlib import Path


STATIC = Path(__file__).parents[1] / "src" / "codebase_os" / "static"


def test_ui_has_authenticated_workspace_structure():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'href="#workspace"' in html
    assert 'id="repository-select"' in html
    assert 'id="query-form"' in html
    assert 'id="session-status"' in html
    assert 'id="evidence-rail"' in html
    assert 'id="skip-link"' in html


def test_ui_exposes_operational_states_and_controls():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    script = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "Loading repositories" in html
    assert "No repositories indexed" in html + script
    assert "Permission denied" in html + script
    assert "Delete repository" in html
    assert "aria-live" in html
    assert "api/repositories" in script
    assert "api/repositories/index" in script


def test_ui_styles_define_accessible_responsive_workspace():
    styles = (STATIC / "styles.css").read_text(encoding="utf-8")
    assert ":focus-visible" in styles
    assert "prefers-reduced-motion" in styles
    assert "max-width:768px" in styles
