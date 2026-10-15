from app.ml.model_loader import load_explainer, load_metadata
from app.ml.predictor import build_feature_vector, format_factor_value

def explain_prediction(district: dict, scenario: str):
    district_id = district.get("districtId") or district.get("id") or ""
    vector, feat_dict, _ = build_feature_vector(str(district_id), scenario)
    explainer = load_explainer()
    metadata = load_metadata()

    if explainer is not None and metadata is not None and vector is not None and feat_dict is not None:
        try:
            sv = explainer(vector).values[0]
            cols = metadata["feature_columns"]
            meta_feat = metadata["feature_metadata"]

            raw_factors = []
            for i, col in enumerate(cols):
                shap_val = float(sv[i])
                val_num = feat_dict[col]
                disp = meta_feat.get(col, {}).get("display_name", col)
                raw_factors.append({
                    "feature": disp,
                    "abs_importance": abs(shap_val),
                    "value": format_factor_value(col, val_num),
                    "impact": "positive" if shap_val >= 0 else "negative",
                })

            raw_factors.sort(key=lambda x: x["abs_importance"], reverse=True)
            top = raw_factors[:5]
            total_imp = sum(f["abs_importance"] for f in top)
            if total_imp <= 0:
                total_imp = 1.0

            factors = []
            for f in top:
                contrib = round((f["abs_importance"] / total_imp) * 100.0, 1)
                factors.append({
                    "feature": f["feature"],
                    "contribution": contrib,
                    "value": f["value"],
                    "impact": f["impact"],
                })

            return {
                "prediction_id": 0,
                "main_factors": factors,
            }
        except Exception:
            pass

    # Fallback jika model atau explainer tidak tersedia
    factors = [
        {
            "feature": f["factor"],
            "contribution": float(f["contribution"]),
            "value": f["value"],
            "impact": "positive",
        }
        for f in district.get("factors", [])
    ]
    return {
        "prediction_id": 0,
        "main_factors": sorted(factors, key=lambda x: x["contribution"], reverse=True),
    }

