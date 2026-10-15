from app.services.seed import MOCK_RECOMMENDATIONS, MOCK_DISTRICTS

def list_recommendations(risk: str | None = None, q: str | None = None):
    rows = MOCK_RECOMMENDATIONS
    if risk and risk != "all":
        rows = [r for r in rows if r["risk"] == risk]
    if q:
        rows = [r for r in rows if q.lower() in r["area"].lower()]
    return rows

def get_for_area(area_id: str):
    return next((r for r in MOCK_RECOMMENDATIONS if r["areaId"] == area_id), None)

def infer_for_district(district: dict):
    base = get_for_area(district["districtId"])
    if base:
        return base
    score = district["score"]
    level = district["riskLevel"]
    if level == "high":
        return {"areaId": district["districtId"], "area": district["district"], "risk": level, "priority": 99, "action": "Improve drainage capacity", "estimatedImpact": "High", "reason": "Low drainage density"}
    if level == "medium":
        return {"areaId": district["districtId"], "area": district["district"], "risk": level, "priority": 99, "action": "Monitor and desilt drains", "estimatedImpact": "Medium", "reason": "Seasonal risk"}
    return {"areaId": district["districtId"], "area": district["district"], "risk": level, "priority": 99, "action": "Routine monitoring", "estimatedImpact": "Low", "reason": "Stable"}
