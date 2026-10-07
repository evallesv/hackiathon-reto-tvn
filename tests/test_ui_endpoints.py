"""Test suite for the Web Dashboard interface endpoints."""

from fastapi.testclient import TestClient

from hackiathon_reto_tvn.main import app


def test_dashboard_root_serves_html() -> None:
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "TVN MEDIA" in resp.text
    assert "Copiloto de Inteligencia Informativa" in resp.text


def test_dashboard_alias_serves_html() -> None:
    client = TestClient(app)
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "view-agenda" in resp.text


def test_static_assets_served() -> None:
    client = TestClient(app)

    # Stylesheet
    resp_css = client.get("/static/styles.css")
    assert resp_css.status_code == 200
    assert "text/css" in resp_css.headers["content-type"]
    assert "--tvn-red" in resp_css.text

    # JavaScript logic
    resp_js = client.get("/static/app.js")
    assert resp_js.status_code == 200
    assert "javascript" in resp_js.headers["content-type"]
    assert "selectFicha" in resp_js.text
