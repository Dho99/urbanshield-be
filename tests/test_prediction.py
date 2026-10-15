"""
Test suite for ML prediction and SHAP explanation pipeline.
"""
import pytest
from app.ml.model_loader import load_model, load_explainer, load_metadata, DISTRICTS_PATH
from app.ml.predictor import build_feature_vector, predict_for_district, format_factor_value
from app.ml.explainer import explain_prediction


def test_model_and_artifacts_loaded():
    """Memastikan model.pkl, explainer.pkl, dan metadata.json valid dan terisi."""
    model = load_model()
    explainer = load_explainer()
    metadata = load_metadata()

    assert model is not None, "Model XGBoost tidak boleh None"
    assert explainer is not None, "SHAP Explainer tidak boleh None"
    assert metadata is not None, "Metadata JSON tidak boleh None"
    assert "feature_columns" in metadata
    assert len(metadata["feature_columns"]) >= 10


def test_feature_vector_generation():
    """Memastikan feature vector untuk kecamatan Kota Bandung valid dan 14 dimensi."""
    metadata = load_metadata()
    cols = metadata["feature_columns"]

    vec, feat_dict, district_info = build_feature_vector("coblong", "current")
    assert vec is not None
    assert vec.shape == (1, len(cols))
    assert feat_dict["rainfall_mm"] == 0.0 or feat_dict["rainfall_mm"] >= 0.0
    assert feat_dict["elevation_mean"] > 600.0  # Elevasi Bandung > 600m

    # Uji skenario heavy_rain_24h
    vec_rain, feat_rain, _ = build_feature_vector("coblong", "heavy_rain_24h")
    assert feat_rain["rainfall_mm"] > feat_dict["rainfall_mm"]


def test_predict_for_district_scenarios():
    """Memastikan prediksi berjalan untuk seluruh 4 skenario dan score berkisar 0-100."""
    scenarios = ["current", "heavy_rain_24h", "heavy_rain_72h", "drainage_failure"]
    scores = {}

    for sc in scenarios:
        res = predict_for_district("gedebage", sc)
        assert res is not None
        assert "score" in res
        assert 0 <= res["score"] <= 100
        assert res["riskLevel"] in ["low", "medium", "high"]
        scores[sc] = res["score"]

    # Skenario hujan ekstrem harus meningkatkan atau sama dengan risk score
    assert scores["heavy_rain_72h"] >= scores["current"]


def test_shap_explanation_structure():
    """Memastikan SHAP explanation menghasilkan faktor pendorong yang terformat rapi."""
    res = predict_for_district("cidadap", "current")
    assert res is not None

    expl = explain_prediction(res, "current")
    assert "main_factors" in expl
    assert len(expl["main_factors"]) > 0

    first_factor = expl["main_factors"][0]
    assert "feature" in first_factor
    assert "contribution" in first_factor
    assert "value" in first_factor
    assert first_factor["impact"] in ["positive", "negative"]


def test_format_factor_value():
    """Memastikan utilitas format nilai fitur berfungsi sesuai metadata satuan."""
    val_rf = format_factor_value("rainfall_mm", 125.4)
    assert "mm / 24h" in val_rf

    val_elev = format_factor_value("elevation_mean", 725.0)
    assert "m" in val_elev
