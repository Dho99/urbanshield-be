"""Tests for rule-based mitigation engine: deterministic SHAP -> actions."""
from app.services.mitigation_engine import build_decision


def _f(factor, contribution, value="1.0"):
    return {"factor": factor, "contribution": contribution, "value": value}


def test_drainage_dominant_recommends_drainage():
    d = build_decision("andir", "Andir", 50, "medium", 86, [
        _f("Effective drainage capacity", 41, "0.6 km/km²"),
        _f("Population density", 29, "24.9k/km²"),
        _f("Drainage density", 18, "0.7 km/km²"),
        _f("Road network density", 12, "2.9 km/km²"),
    ])
    assert d["risk_summary"]["score"] == 50
    assert d["headline_action"] == "Normalisasi drainase utama"
    assert d["actions"][0]["priority"] == "High"
    assert "41" in d["why_this_action"][0]["reason"]
    assert len(d["supporting_data"]) == 4


def test_population_high_risk_evacuates():
    d = build_decision("x", "X", 82, "high", 90, [
        _f("Population density", 35, "14.2k/km²"),
        _f("Rainfall intensity", 30, "142 mm / 24h"),
        _f("Elevation", 20, "691 m"),
        _f("Drainage density", 15, "0.8 km/km²"),
    ])
    titles = [a["title"] for a in d["actions"]]
    assert "Kesiapsiagaan evakuasi + early warning" in titles


def test_low_elevation_flood_infrastructure():
    d = build_decision("x", "X", 65, "medium", 80, [
        _f("Elevation", 30, "690 m"),
        _f("Basin depression level", 25, "0.8 index"),
        _f("Rainfall intensity", 25, "100 mm / 24h"),
        _f("Green infiltration area", 20, "5.0%"),
    ])
    titles = [a["title"] for a in d["actions"]]
    assert "Infrastruktur pengendali banjir" in titles
    assert "Optimalisasi area resapan" in titles


def test_deterministic_and_always_monitoring():
    factors = [_f("Road network density", 40, "3.0 km/km²"), _f("Elevation", 30, "700 m")]
    a = build_decision("x", "X", 30, "low", 80, factors)
    b = build_decision("x", "X", 30, "low", 80, factors)
    assert a == b
    assert a["actions"][-1]["title"] == "Monitoring area rawan genangan"
    assert a["actions"][-1]["priority"] == "Low"


def test_empty_factors_safe():
    d = build_decision("x", "X", 42, "medium", 78, [])
    assert d["why_this_action"] == []
    assert d["supporting_data"] == []
    assert len(d["actions"]) >= 1
