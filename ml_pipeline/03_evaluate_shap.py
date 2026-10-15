"""
03_evaluate_shap.py
Script evaluasi mendalam SHAP (SHapley Additive exPlanations) untuk model UrbanShield AI.
Menghasilkan:
1. SHAP Summary Plot (Beeswarm)
2. SHAP Feature Importance Bar Chart
3. SHAP Dependence Plots (Rainfall, Elevation, Drainage)
4. Case Study Waterfall / Bar untuk 5 kecamatan representatif (Gedebage, Coblong, Babakan Ciparay, Cidadap, Arcamanik)
5. Ringkasan analisis interpretasi untuk laporan ICONFEST
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

# Tambahkan backend ke path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.model_loader import load_model, load_explainer, load_metadata, DISTRICTS_PATH

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_shap_evaluation():
    print("=" * 60)
    print("UrbanShield AI - SHAP Detailed Evaluation & Interpretation")
    print("=" * 60)

    model = load_model()
    explainer = load_explainer()
    metadata = load_metadata()

    if model is None or explainer is None or metadata is None:
        print("[ERROR] Model, explainer, atau metadata tidak ditemukan di app/ml/artifacts!")
        sys.exit(1)

    feature_cols = metadata["feature_columns"]
    data_path = Path(__file__).resolve().parent / "data" / "training_dataset.csv"
    if not data_path.exists():
        data_path = Path(__file__).resolve().parent / "data" / "training_dataset_v2.csv"

    print(f"Loading dataset: {data_path}")
    df = pd.read_csv(data_path)
    X = df[feature_cols]
    y = df["risk_score"]

    # Hitung SHAP values
    print("Menghitung SHAP values...")
    shap_explanation = explainer(X)
    shap_values = shap_explanation.values

    # 1. Summary Plot (Beeswarm)
    import shap
    print("Menyimpan SHAP Summary Plot (Beeswarm)...")
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X, feature_names=feature_cols, show=False)
    plt.title("UrbanShield AI - SHAP Feature Impact (Beeswarm Plot)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    summary_path = RESULTS_DIR / "shap_summary.png"
    plt.savefig(summary_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {summary_path}")

    # 2. Global Feature Importance Bar Chart
    print("Menyimpan SHAP Feature Importance Bar Chart...")
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X, feature_names=feature_cols, plot_type="bar", show=False)
    plt.title("UrbanShield AI - Mean |SHAP Value| (Global Importance)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    bar_path = RESULTS_DIR / "shap_importance.png"
    plt.savefig(bar_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {bar_path}")

    # 3. Dependence Plots untuk fitur utama
    print("Menyimpan SHAP Dependence Plots...")
    for feat in ["rainfall_mm", "elevation_mean", "effective_drainage_capacity"]:
        if feat in feature_cols:
            plt.figure(figsize=(8, 5))
            shap.dependence_plot(
                feat,
                shap_values,
                X,
                feature_names=feature_cols,
                show=False,
            )
            plt.title(f"SHAP Dependence Plot: {feat}", fontsize=12, fontweight="bold")
            plt.tight_layout()
            dep_path = RESULTS_DIR / f"shap_dependence_{feat}.png"
            plt.savefig(dep_path, dpi=180, bbox_inches="tight")
            plt.close()
            print(f"Saved: {dep_path}")

    # 4. District Case Studies
    print("\nMelakukan analisis studi kasus per kecamatan representatif...")
    case_districts = ["gedebage", "coblong", "babakan-ciparay", "cidadap", "arcamanik"]
    districts_features = {}
    if DISTRICTS_PATH.exists():
        districts_features = json.loads(DISTRICTS_PATH.read_text(encoding="utf-8"))

    case_study_results = []
    for dist_id in case_districts:
        feat_data = districts_features.get(dist_id)
        if not feat_data:
            continue
        
        # Buat vektor fitur baseline
        vec = np.array([[feat_data.get(c, 0.0) for c in feature_cols]])
        pred_val = float(model.predict(vec)[0])
        dist_shap = explainer(vec).values[0]

        # Top 3 pendorong positif dan penurun risiko
        drivers = []
        for i, col in enumerate(feature_cols):
            sv = float(dist_shap[i])
            drivers.append({
                "feature": col,
                "display_name": metadata["feature_metadata"].get(col, {}).get("display_name", col),
                "shap_value": sv,
                "abs_val": abs(sv),
                "val": float(vec[0][i]),
                "unit": metadata["feature_metadata"].get(col, {}).get("unit", "")
            })
        drivers.sort(key=lambda d: d["abs_val"], reverse=True)

        case_study_results.append({
            "district_id": dist_id,
            "district_name": feat_data.get("district_name", dist_id.title()),
            "predicted_risk_score": round(pred_val, 1),
            "top_drivers": drivers[:4]
        })

    # Simpan hasil evaluasi ke JSON
    eval_json_path = RESULTS_DIR / "shap_evaluation_summary.json"
    eval_summary = {
        "dataset_rows": len(df),
        "features_evaluated": len(feature_cols),
        "mean_absolute_shap": {
            col: round(float(np.mean(np.abs(shap_values[:, i]))), 4)
            for i, col in enumerate(feature_cols)
        },
        "case_studies": case_study_results
    }
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)
    print(f"\nSaved evaluation summary JSON: {eval_json_path}")

    # Print ringkasan
    print("\n--- RINGKASAN GLOBAL SHAP IMPORTANCE ---")
    sorted_feats = sorted(eval_summary["mean_absolute_shap"].items(), key=lambda x: x[1], reverse=True)
    for rank, (feat, score) in enumerate(sorted_feats, 1):
        print(f"{rank:2d}. {feat:28s}: {score:.4f}")

    print("\n--- STUDI KASUS KECAMATAN REPRESENTATIF ---")
    for cs in case_study_results:
        print(f"\n[{cs['district_name']}] - Predicted Risk: {cs['predicted_risk_score']}")
        for d in cs["top_drivers"]:
            sign = "+" if d["shap_value"] >= 0 else "-"
            print(f"  {sign} {d['display_name']} ({d['val']} {d['unit']}): SHAP={d['shap_value']:+.3f}")

    print("\nEvaluasi SHAP selesai dengan sukses!")


if __name__ == "__main__":
    run_shap_evaluation()
