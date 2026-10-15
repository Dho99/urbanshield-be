"""
Test suite for FastAPI endpoints via TestClient.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Endpoint health check harus return status ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"


def test_dashboard_overview():
    """Endpoint dashboard overview harus mengembalikan metrik agregat."""
    resp = client.get("/api/v1/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "totalMonitored" in data
    assert "highRisk" in data
    assert "mediumRisk" in data
    assert "lowRisk" in data
    assert data["totalMonitored"] >= 8


def test_map_risk_layer():
    """Endpoint map risk-layer harus mengembalikan GeoJSON FeatureCollection."""
    resp = client.get("/api/v1/map/risk-layer")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("type") == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) > 0


def test_predictions_districts():
    """Endpoint predictions/districts harus mengembalikan list distrik."""
    resp = client.get("/api/v1/predictions/districts")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 8


def test_post_prediction():
    """Endpoint POST /api/v1/predictions harus sukses memprediksi risiko."""
    payload = {
        "districtId": "gedebage",
        "scenario": "heavy_rain_24h"
    }
    resp = client.post("/api/v1/predictions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["districtId"] == "gedebage"
    assert "score" in data
    assert "riskLevel" in data
    assert "factors" in data


def test_prediction_explanation():
    """Endpoint SHAP explanation harus mengembalikan main_factors."""
    resp = client.get("/api/v1/predictions/1/explanation?districtId=coblong&scenario=current")
    assert resp.status_code == 200
    data = resp.json()
    assert "main_factors" in data
    assert len(data["main_factors"]) > 0


def test_recommendations_list():
    """Endpoint recommendations harus mengembalikan daftar rekomendasi."""
    resp = client.get("/api/v1/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "action" in data[0]


def test_recommendation_by_area():
    """Endpoint recommendation by area id harus mengembalikan rekomendasi spesifik."""
    resp = client.get("/api/v1/recommendations/gedebage")
    assert resp.status_code == 200
    data = resp.json()
    assert data["areaId"] == "gedebage"
    assert "action" in data


def test_datasets_catalog():
    """Endpoint catalog dataset harus mengembalikan list sumber data."""
    resp = client.get("/api/v1/datasets")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
