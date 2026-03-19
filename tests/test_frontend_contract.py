from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_react_frontend_contract_exists():
    app = (ROOT / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")
    package = (ROOT / "frontend" / "package.json").read_text(encoding="utf-8")

    assert "react" in package
    assert "/ask" in app
    assert "/patients/search" in app
    assert "/index/status" in app
    assert "/review/gap" in app


def test_frontend_uses_enterprise_section_labels():
    app = (ROOT / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")
    for label in [
        "AI Assistant for Clinical Gap Intelligence",
        "Care Gaps",
        "Documentation",
        "Revenue & Quality",
        "Evidence",
        "Patient Timeline",
        "Audit Trail",
    ]:
        assert label in app
