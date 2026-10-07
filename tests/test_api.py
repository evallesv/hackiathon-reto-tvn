"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from hackiathon_reto_tvn.main import app

client = TestClient(app)


def test_healthz_endpoint() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "hackiathon-reto-tvn"
    assert "decision_provider" in data


def test_system_info_endpoint() -> None:
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "hackiathon-reto-tvn"
    assert "llm_provider" in data
    assert "llm_model" in data
    assert "decision_provider" in data
    assert "decision_model" in data


def test_contradictions_endpoint() -> None:
    response = client.post(
        "/api/v1/copilot/contradictions",
        json={
            "texto_a": "Fuente A afirma 15 millones de inversión",
            "texto_b": "Fuente B afirma 28 millones de inversión",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["discrepancia_detectada"] is True
    assert data["estado"] == "requiere_evidencia"


def test_agenda_endpoint() -> None:
    response = client.get("/api/v1/copilot/agenda?top_n=3")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    if data:
        assert "id_caso" in data[0]
        assert "puntaje" in data[0]
        assert "componentes" in data[0]


def test_manifest_endpoint() -> None:
    response = client.get("/api/v1/copilot/manifest")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v1.0"
    assert "archivos" in data
    assert "fecha_corte_utc" in data
    assert "fecha_corte_UTC" not in data


def test_ingestion_endpoints() -> None:
    # Status endpoint
    resp_status = client.get("/api/v1/ingestion/status")
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert "db_path" in status_data
    assert "total_noticias" in status_data

    # Noticias endpoint
    resp_noticias = client.get("/api/v1/ingestion/noticias?limit=5")
    assert resp_noticias.status_code == 200
    assert isinstance(resp_noticias.json(), list)
