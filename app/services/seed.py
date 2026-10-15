import json
from pathlib import Path
from datetime import datetime, timezone

ARTIFACT_PATH = Path(__file__).resolve().parent.parent / "ml" / "artifacts" / "districts_30_seed.json"

def _load_data():
    if ARTIFACT_PATH.exists():
        try:
            data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
            if len(data.get("districts", [])) >= 30:
                return data["districts"], data["risk_layer"], data["recommendations"]
        except Exception:
            pass
    return None, None, None

def get_mock_risk_layer():
    _, rl, _ = _load_data()
    return rl if rl else MOCK_RISK_LAYER

def get_mock_districts():
    d, _, _ = _load_data()
    return d if d else MOCK_DISTRICTS

def get_mock_recommendations():
    _, _, r = _load_data()
    return r if r else MOCK_RECOMMENDATIONS

_districts, _risk_layer, _recommendations = _load_data()
if _districts is not None:
    MOCK_DISTRICTS = _districts
    MOCK_RISK_LAYER = _risk_layer
    MOCK_RECOMMENDATIONS = _recommendations
else:
    MOCK_DISTRICTS = [
        {"districtId": "coblong", "district": "Coblong", "riskLevel": "high", "score": 82, "confidence": 87, "factors": [{"factor": "Rainfall intensity", "contribution": 35, "value": "142 mm / 24h"}, {"factor": "Drainage density", "contribution": 28, "value": "0.8 km / km²"}, {"factor": "Elevation", "contribution": 20, "value": "691 m"}, {"factor": "Population density", "contribution": 17, "value": "14.2k / km²"}], "recommendation": "Improve drainage capacity along the Cikapundung corridor."},
        {"districtId": "sukajadi", "district": "Sukajadi", "riskLevel": "high", "score": 76, "confidence": 83, "factors": [{"factor": "Rainfall intensity", "contribution": 33, "value": "128 mm / 24h"}, {"factor": "Drainage density", "contribution": 30, "value": "0.9 km / km²"}, {"factor": "Elevation", "contribution": 19, "value": "698 m"}, {"factor": "Population density", "contribution": 18, "value": "12.8k / km²"}], "recommendation": "Prioritize retention pond construction in low-lying blocks."},
        {"districtId": "cicendo", "district": "Cicendo", "riskLevel": "medium", "score": 58, "confidence": 79, "factors": [{"factor": "Rainfall intensity", "contribution": 30, "value": "96 mm / 24h"}, {"factor": "Drainage density", "contribution": 27, "value": "1.4 km / km²"}, {"factor": "Elevation", "contribution": 23, "value": "704 m"}, {"factor": "Population density", "contribution": 20, "value": "11.1k / km²"}], "recommendation": "Routine drain desilting before peak rainy season."},
        {"districtId": "andir", "district": "Andir", "riskLevel": "medium", "score": 54, "confidence": 81, "factors": [{"factor": "Rainfall intensity", "contribution": 31, "value": "91 mm / 24h"}, {"factor": "Drainage density", "contribution": 26, "value": "1.5 km / km²"}, {"factor": "Elevation", "contribution": 22, "value": "708 m"}, {"factor": "Population density", "contribution": 21, "value": "10.4k / km²"}], "recommendation": "Monitor riverbank sections near Citepus sub-catchment."},
        {"districtId": "bandung-wetan", "district": "Bandung Wetan", "riskLevel": "medium", "score": 49, "confidence": 77, "factors": [{"factor": "Rainfall intensity", "contribution": 29, "value": "84 mm / 24h"}, {"factor": "Drainage density", "contribution": 25, "value": "1.7 km / km²"}, {"factor": "Elevation", "contribution": 24, "value": "712 m"}, {"factor": "Population density", "contribution": 22, "value": "9.6k / km²"}], "recommendation": "Maintain existing pump stations at design capacity."},
        {"districtId": "sumur-bandung", "district": "Sumur Bandung", "riskLevel": "low", "score": 32, "confidence": 85, "factors": [{"factor": "Rainfall intensity", "contribution": 28, "value": "61 mm / 24h"}, {"factor": "Drainage density", "contribution": 24, "value": "2.1 km / km²"}, {"factor": "Elevation", "contribution": 26, "value": "718 m"}, {"factor": "Population density", "contribution": 22, "value": "8.9k / km²"}], "recommendation": "No priority action. Continue routine monitoring."},
        {"districtId": "cibeunying-kidul", "district": "Cibeunying Kidul", "riskLevel": "low", "score": 28, "confidence": 88, "factors": [{"factor": "Rainfall intensity", "contribution": 27, "value": "55 mm / 24h"}, {"factor": "Drainage density", "contribution": 23, "value": "2.3 km / km²"}, {"factor": "Elevation", "contribution": 28, "value": "725 m"}, {"factor": "Population density", "contribution": 22, "value": "7.4k / km²"}], "recommendation": "No priority action. Continue routine monitoring."},
        {"districtId": "cidadap", "district": "Cidadap", "riskLevel": "low", "score": 24, "confidence": 90, "factors": [{"factor": "Rainfall intensity", "contribution": 26, "value": "49 mm / 24h"}, {"factor": "Drainage density", "contribution": 22, "value": "2.5 km / km²"}, {"factor": "Elevation", "contribution": 30, "value": "812 m"}, {"factor": "Population density", "contribution": 22, "value": "5.1k / km²"}], "recommendation": "No priority action. Continue routine monitoring."},
    ]
    CELLS = [(107.615, -6.895), (107.635, -6.895), (107.595, -6.9), (107.615, -6.91), (107.635, -6.91), (107.615, -6.925), (107.635, -6.925), (107.605, -6.878)]

    def rect(cx, cy, w=0.018, h=0.014):
        return [[[cx - w/2, cy - h/2], [cx + w/2, cy - h/2], [cx + w/2, cy + h/2], [cx - w/2, cy + h/2], [cx - w/2, cy - h/2]]]

    MOCK_RISK_LAYER = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"districtId": d["districtId"], "district": d["district"], "riskLevel": d["riskLevel"], "score": d["score"]}, "geometry": {"type": "Polygon", "coordinates": rect(CELLS[i][0], CELLS[i][1])}} for i, d in enumerate(MOCK_DISTRICTS)]}

    MOCK_RECOMMENDATIONS = [
        {"areaId": "coblong", "area": "Coblong", "risk": "high", "priority": 1, "action": "Drainage improvement", "estimatedImpact": "High", "reason": "Low drainage density"},
        {"areaId": "sukajadi", "area": "Sukajadi", "risk": "high", "priority": 2, "action": "Retention pond construction", "estimatedImpact": "High", "reason": "Low-lying blocks"},
        {"areaId": "cicendo", "area": "Cicendo", "risk": "medium", "priority": 3, "action": "Drain desilting program", "estimatedImpact": "Medium", "reason": "Seasonal siltation"},
        {"areaId": "andir", "area": "Andir", "risk": "medium", "priority": 4, "action": "Riverbank monitoring", "estimatedImpact": "Medium", "reason": "Citepus sub-catchment"},
        {"areaId": "bandung-wetan", "area": "Bandung Wetan", "risk": "medium", "priority": 5, "action": "Pump station maintenance", "estimatedImpact": "Medium", "reason": "Capacity check"},
        {"areaId": "sumur-bandung", "area": "Sumur Bandung", "risk": "low", "priority": 6, "action": "Routine monitoring", "estimatedImpact": "Low", "reason": "Stable"},
    ]

SCENARIO_MULTIPLIER = {"current": 1.0, "heavy_rain_24h": 1.15, "heavy_rain_72h": 1.30, "drainage_failure": 1.20}
SCENARIO_LABEL = {
    "current": "Kondisi Eksisting (Normal)",
    "heavy_rain_24h": "Hujan Lebat 1 Hari (24 Jam)",
    "heavy_rain_72h": "Hujan Deras 3 Hari Berturut-turut (72 Jam)",
    "drainage_failure": "Kegagalan Sistem Drainase",
}

def risk_level(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"

def now_iso():
    return datetime.now(timezone.utc).isoformat()
