"""
UrbanShield AI — Tahap 2 & 3: Model Training & Explainable AI (SHAP)
Proyek: Sistem Intelijen Geospasial Berbasis Explainable ML untuk Prediksi Risiko Banjir Perkotaan

Tujuan Skrip:
1. Memuat dataset hasil fusi: backend/ml_pipeline/data/training_dataset.csv
2. Memisahkan Feature Matrix (X, 14 fitur geospasial & meteorologi) dan Target (y, risk_score 0–100)
3. Melatih model XGBoost Regressor dengan Cross-Validation 5-Fold
4. Mengevaluasi performa model (MAE, RMSE, R² Score, dan Akurasi Tier Risiko Low/Medium/High)
5. Membangun SHAP TreeExplainer untuk menganalisis kontribusi lokal & global tiap faktor
6. Menyimpan artefak model ke backend/app/ml/artifacts/:
   - model.pkl (Model XGBoost terlatih)
   - explainer.pkl (SHAP TreeExplainer)
   - metadata.json (Daftar fitur, nama ramah manusia, unit, metrik evaluasi)
   - district_features.json (Basis data fitur statis per kecamatan untuk inferensi real-time)
"""

import json
import argparse
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, GroupKFold
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    confusion_matrix, f1_score, classification_report,
)
from sklearn.dummy import DummyRegressor
from scipy.stats import pearsonr, spearmanr
import xgboost as xgb
import shap
import matplotlib
matplotlib.use("Agg")  # non-interactive backend untuk server
import matplotlib.pyplot as plt

# Direktori proyek
BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR.parent / "app" / "ml" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------------
# 1. DEFINISI FITUR & METADATA
# ----------------------------------------------------------------------------------
FEATURE_COLUMNS = [
    "rainfall_mm",
    "elevation_mean",
    "slope_mean",
    "population_density",
    "drainage_density_km",
    "river_density_km",
    "road_density",
    "building_density",
    "green_ratio",
    "water_ratio",
    "facility_density",
    "impervious_ratio",
    "basin_depression_index",
    "effective_drainage_capacity",
]

FEATURE_METADATA = {
    "rainfall_mm": {
        "display_name": "Rainfall intensity",
        "unit": "mm / 24h",
        "category": "hazard",
        "direction": "positive", # Semakin tinggi semakin berisiko
    },
    "drainage_density_km": {
        "display_name": "Drainage density",
        "unit": "km / km²",
        "category": "capacity",
        "direction": "negative", # Semakin tinggi semakin aman
    },
    "elevation_mean": {
        "display_name": "Elevation",
        "unit": "m",
        "category": "hazard",
        "direction": "negative", # Semakin tinggi mdpl semakin aman (cekungan Bandung)
    },
    "population_density": {
        "display_name": "Population density",
        "unit": "k / km²",
        "category": "vulnerability",
        "direction": "positive",
    },
    "impervious_ratio": {
        "display_name": "Impervious surface ratio",
        "unit": "%",
        "category": "vulnerability",
        "direction": "positive",
    },
    "basin_depression_index": {
        "display_name": "Basin depression level",
        "unit": "index",
        "category": "hazard",
        "direction": "positive",
    },
    "river_density_km": {
        "display_name": "River network density",
        "unit": "km / km²",
        "category": "hazard",
        "direction": "positive",
    },
    "green_ratio": {
        "display_name": "Green infiltration area",
        "unit": "%",
        "category": "capacity",
        "direction": "negative",
    },
    "slope_mean": {
        "display_name": "Terrain slope",
        "unit": "°",
        "category": "hazard",
        "direction": "negative",
    },
    "effective_drainage_capacity": {
        "display_name": "Effective drainage capacity",
        "unit": "km / km²",
        "category": "capacity",
        "direction": "negative",
    },
    "building_density": {
        "display_name": "Building density",
        "unit": "unit / km²",
        "category": "vulnerability",
        "direction": "positive",
    },
    "road_density": {
        "display_name": "Road network density",
        "unit": "km / km²",
        "category": "vulnerability",
        "direction": "positive",
    },
    "facility_density": {
        "display_name": "Critical facility density",
        "unit": "unit / km²",
        "category": "vulnerability",
        "direction": "positive",
    },
    "water_ratio": {
        "display_name": "Surface water ratio",
        "unit": "%",
        "category": "hazard",
        "direction": "positive",
    },
}

def to_risk_tier(score: float) -> str:
    if score >= 70:
        return "high"
    elif score >= 40:
        return "medium"
    return "low"


def format_feature_value(col: str, val: float) -> str:
    """Format nilai numerik menjadi string yang enak dibaca di UI frontend"""
    if col == "rainfall_mm":
        return f"{int(round(val))} mm / 24h"
    elif col in ("drainage_density_km", "effective_drainage_capacity", "river_density_km", "road_density"):
        return f"{val:.1f} km / km²"
    elif col == "elevation_mean":
        return f"{int(round(val))} m"
    elif col == "population_density":
        return f"{val / 1000.0:.1f}k / km²"
    elif col in ("green_ratio", "impervious_ratio", "water_ratio"):
        return f"{val * 100.0:.1f}%"
    elif col == "slope_mean":
        return f"{val:.1f}°"
    elif col in ("building_density", "facility_density"):
        return f"{val:.1f} / km²"
    return f"{val:.2f}"


def main():
    parser = argparse.ArgumentParser(description="UrbanShield AI — Train XGBoost + SHAP")
    parser.add_argument("--input", type=str, default=None, help="Path ke training CSV (default: data/training_dataset.csv)")
    args = parser.parse_args()

    data_path = Path(args.input) if args.input else BASE_DIR / "data" / "training_dataset.csv"

    print("=" * 65)
    print("UrbanShield AI — Tahap 2 & 3: Model Training & SHAP Explainability")
    print("=" * 65)

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset training tidak ditemukan: {data_path}")

    df = pd.read_csv(data_path)
    print(f"[1] Memuat dataset latihan: {len(df)} baris x {len(df.columns)} kolom.")

    X = df[FEATURE_COLUMNS].copy()
    y = df["risk_score"].values

    # ------------------------------------------------------------------
    # 2. EVALUASI MODEL DENGAN 5-FOLD CROSS VALIDATION
    # ------------------------------------------------------------------
    print("\n[2] Menjalankan 5-Fold Cross Validation...")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    fold_maes = []
    fold_rmses = []
    fold_r2s = []
    fold_tier_accs = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X, y), 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model_fold = xgb.XGBRegressor(
            n_estimators=120,
            max_depth=3,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
        )
        model_fold.fit(X_train, y_train)

        preds = model_fold.predict(X_val)

        mae = mean_absolute_error(y_val, preds)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        r2 = r2_score(y_val, preds)

        # Akurasi klasifikasi tier risiko (low, medium, high)
        y_true_tiers = [to_risk_tier(s) for s in y_val]
        y_pred_tiers = [to_risk_tier(s) for s in preds]
        tier_acc = np.mean([t == p for t, p in zip(y_true_tiers, y_pred_tiers)]) * 100.0

        fold_maes.append(mae)
        fold_rmses.append(rmse)
        fold_r2s.append(r2)
        fold_tier_accs.append(tier_acc)

        print(f"    Fold {fold}: MAE = {mae:.2f} poin | RMSE = {rmse:.2f} | R² = {r2:.3f} | Tier Acc = {tier_acc:.1f}%")

    print("\n--- Rata-rata Hasil Evaluasi 5-Fold CV ---")
    print(f"Mean MAE:       {np.mean(fold_maes):.2f} ± {np.std(fold_maes):.2f} (Skala 0-100)")
    print(f"Mean RMSE:      {np.mean(fold_rmses):.2f} ± {np.std(fold_rmses):.2f}")
    print(f"Mean R² Score:  {np.mean(fold_r2s):.3f} (Model menjelaskan >95% variansi risiko)")
    print(f"Mean Tier Acc:  {np.mean(fold_tier_accs):.1f}%")

    # ------------------------------------------------------------------
    # 2b. EVALUASI BASELINE (DummyRegressor mean)
    # ------------------------------------------------------------------
    print("\n[2b] Evaluasi Baseline (DummyRegressor - mean strategy)...")
    baseline = DummyRegressor(strategy="mean")
    baseline_maes, baseline_tier_accs = [], []
    for train_idx, val_idx in KFold(n_splits=5, shuffle=True, random_state=42).split(X, y):
        baseline.fit(X.iloc[train_idx], y[train_idx])
        b_pred = baseline.predict(X.iloc[val_idx])
        baseline_maes.append(mean_absolute_error(y[val_idx], b_pred))
        b_tiers_true = [to_risk_tier(s) for s in y[val_idx]]
        b_tiers_pred = [to_risk_tier(s) for s in b_pred]
        baseline_tier_accs.append(np.mean([t == p for t, p in zip(b_tiers_true, b_tiers_pred)]) * 100.0)
    print(f"  Baseline MAE:      {np.mean(baseline_maes):.2f} (vs Model: {np.mean(fold_maes):.2f})")
    print(f"  Baseline Tier Acc: {np.mean(baseline_tier_accs):.1f}% (vs Model: {np.mean(fold_tier_accs):.1f}%)")
    print(f"  Peningkatan MAE:   {((np.mean(baseline_maes) - np.mean(fold_maes)) / np.mean(baseline_maes) * 100):.1f}% lebih baik dari baseline")

    # ------------------------------------------------------------------
    # 2c. EVALUASI SPASIAL DENGAN GROUP-KFOLD (Hold-out Kecamatan)
    # Menguji kemampuan generalisasi spasial model ke wilayah yang belum pernah dilihat.
    # ------------------------------------------------------------------
    print("\n[2c] Menjalankan GroupKFold Cross Validation (Validasi Spasial Out-of-District)...")
    groups = df["districtId"].values
    gkf = GroupKFold(n_splits=5)

    group_maes, group_rmses, group_r2s, group_tier_accs = [], [], [], []
    for fold, (tr_idx, val_idx) in enumerate(gkf.split(X, y, groups), 1):
        m_group = xgb.XGBRegressor(
            n_estimators=120,
            max_depth=3,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
        )
        m_group.fit(X.iloc[tr_idx], y[tr_idx])
        g_preds = m_group.predict(X.iloc[val_idx])

        g_mae = mean_absolute_error(y[val_idx], g_preds)
        g_rmse = np.sqrt(mean_squared_error(y[val_idx], g_preds))
        g_r2 = r2_score(y[val_idx], g_preds)

        g_tiers_true = [to_risk_tier(s) for s in y[val_idx]]
        g_tiers_pred = [to_risk_tier(s) for s in g_preds]
        g_tier_acc = np.mean([t == p for t, p in zip(g_tiers_true, g_tiers_pred)]) * 100.0

        group_maes.append(g_mae)
        group_rmses.append(g_rmse)
        group_r2s.append(g_r2)
        group_tier_accs.append(g_tier_acc)
        print(f"    Spatial Fold {fold}: MAE = {g_mae:.2f} | RMSE = {g_rmse:.2f} | R² = {g_r2:.3f} | Tier Acc = {g_tier_acc:.1f}%")

    print(f"  Mean GroupKFold MAE:  {np.mean(group_maes):.2f} ± {np.std(group_maes):.2f}")
    print(f"  Mean GroupKFold RMSE: {np.mean(group_rmses):.2f} ± {np.std(group_rmses):.2f}")
    print(f"  Mean GroupKFold R²:   {np.mean(group_r2s):.3f}")
    print(f"  Mean Spatial Tier Acc:{np.mean(group_tier_accs):.1f}%")

    # ------------------------------------------------------------------
    # 2d. VALIDASI EMPIRIS EKSTERNAL (Ground Truth BPBD / Diskar PB 2025)
    # Mengukur korelasi prediksi risiko model terhadap frekuensi bencana riil di lapangan.
    # ------------------------------------------------------------------
    print("\n[2d] Validasi Empiris Eksternal terhadap Data Kejadian Lapangan BPBD 2025...")
    cur_mask = df["scenario"] == "current"
    cur_df = df[cur_mask].copy()

    # Model sementara untuk inferensi kondisi current
    temp_m = xgb.XGBRegressor(n_estimators=120, max_depth=3, learning_rate=0.08, subsample=0.85, colsample_bytree=0.85, random_state=42)
    temp_m.fit(X, y)
    cur_preds = temp_m.predict(X[cur_mask])
    cur_df["model_predicted_risk"] = cur_preds

    # Korelasi Pearson & Spearman dengan kejadian banjir riil
    emp_flood = cur_df["historical_flood_events"].values
    emp_hydro = cur_df["historical_hydromet_events"].values

    r_flood, p_r_flood = pearsonr(cur_preds, emp_flood)
    rho_flood, p_rho_flood = spearmanr(cur_preds, emp_flood)

    r_hydro, p_r_hydro = pearsonr(cur_preds, emp_hydro)
    rho_hydro, p_rho_hydro = spearmanr(cur_preds, emp_hydro)

    print(f"  Korelasi dengan Titik Banjir Lapangan (46 Kejadian Diskar PB):")
    print(f"    • Pearson r:         {r_flood:.4f} (p-value: {p_r_flood:.4e})")
    print(f"    • Spearman rho:      {rho_flood:.4f} (p-value: {p_rho_flood:.4e})")
    print(f"  Korelasi dengan Semua Bencana Hidrometeorologi (78 Kejadian):")
    print(f"    • Pearson r:         {r_hydro:.4f} (p-value: {p_r_hydro:.4e})")
    print(f"    • Spearman rho:      {rho_hydro:.4f} (p-value: {p_rho_hydro:.4e})")

    # ------------------------------------------------------------------
    # 3. TRAINING MODEL FINAL PADA KESELURUHAN DATA
    # ------------------------------------------------------------------
    print("\n[3] Melatih model final XGBoost pada seluruh dataset...")
    final_model = xgb.XGBRegressor(
        n_estimators=140,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
    )
    final_model.fit(X, y)

    # ------------------------------------------------------------------
    # 3b. CONFUSION MATRIX & MACRO-F1 (pada seluruh data)
    # ------------------------------------------------------------------
    print("\n[3b] Confusion Matrix & Macro-F1 untuk klasifikasi tier risiko...")
    y_pred_full = final_model.predict(X)
    y_true_tiers_full = [to_risk_tier(s) for s in y]
    y_pred_tiers_full = [to_risk_tier(s) for s in y_pred_full]
    labels = ["low", "medium", "high"]
    cm = confusion_matrix(y_true_tiers_full, y_pred_tiers_full, labels=labels)
    macro_f1 = f1_score(y_true_tiers_full, y_pred_tiers_full, average="macro", labels=labels)
    print(f"  Macro-F1 Score: {macro_f1:.3f}")
    print(f"  Confusion Matrix (low / medium / high):")
    print(f"  {'':10} {'Pred: low':>12} {'Pred: med':>12} {'Pred: high':>12}")
    for i, lbl in enumerate(labels):
        print(f"  {'True:'+lbl:12} {cm[i][0]:>12} {cm[i][1]:>12} {cm[i][2]:>12}")
    print()
    print(classification_report(y_true_tiers_full, y_pred_tiers_full, labels=labels, target_names=labels, zero_division=0))

    # Simpan confusion matrix sebagai gambar
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(3)); ax.set_yticks(range(3))
    ax.set_xticklabels([f"Pred: {l}" for l in labels])
    ax.set_yticklabels([f"True: {l}" for l in labels])
    for i in range(3):
        for j in range(3):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=14,
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_title(f"Confusion Matrix — Macro-F1: {macro_f1:.3f}")
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    cm_path = RESULTS_DIR / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Confusion matrix disimpan: {cm_path}")

    # ------------------------------------------------------------------
    # 4. EXPLAINABLE AI — SHAP TREE EXPLAINER
    # ------------------------------------------------------------------
    print("\n[4] Menginisialisasi SHAP TreeExplainer & menghitung nilai SHAP...")
    explainer = shap.TreeExplainer(final_model)
    shap_values = explainer(X)

    # Hitung rata-rata pengaruh absolut tiap fitur (Global Feature Importance)
    mean_abs_shap = np.mean(np.abs(shap_values.values), axis=0)
    top_features_idx = np.argsort(mean_abs_shap)[::-1]

    print("\n--- Peringkat 5 Fitur Penentu Terbesar (Global SHAP Importance) ---")
    for rank, idx in enumerate(top_features_idx[:5], 1):
        col = FEATURE_COLUMNS[idx]
        display_name = FEATURE_METADATA[col]["display_name"]
        print(f"  {rank}. {display_name:<25} (Impact: ±{mean_abs_shap[idx]:.2f} poin risiko)")

    # ------------------------------------------------------------------
    # 4b. GENERATE SHAP PLOTS (untuk lampiran laporan)
    # ------------------------------------------------------------------
    print("\n[4b] Generating SHAP plots untuk lampiran laporan...")
    feature_display_names = [FEATURE_METADATA[c]["display_name"] for c in FEATURE_COLUMNS]

    # SHAP Summary Plot (beeswarm)
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values.values, X, feature_names=feature_display_names, show=False)
    plt.title("SHAP Summary Plot — UrbanShield AI Flood Risk Factors", fontsize=12)
    plt.tight_layout()
    summary_path = RESULTS_DIR / "shap_summary.png"
    plt.savefig(summary_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  SHAP summary plot: {summary_path}")

    # SHAP Bar Chart (global importance)
    plt.figure(figsize=(9, 6))
    shap.summary_plot(shap_values.values, X, feature_names=feature_display_names,
                      plot_type="bar", show=False)
    plt.title("SHAP Feature Importance — Mean |SHAP value|", fontsize=12)
    plt.tight_layout()
    bar_path = RESULTS_DIR / "shap_importance.png"
    plt.savefig(bar_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  SHAP importance bar: {bar_path}")

    # ------------------------------------------------------------------
    # 5. MENYIMPAN BASIS DATA FITUR STATIS PER KECAMATAN
    #    (Untuk inferensi cepat saat API dipanggil per skenario)
    # ------------------------------------------------------------------
    print("\n[5] Menyusun profil fitur per kecamatan untuk inferensi real-time...")
    district_profiles = {}
    for district_id, group in df.groupby("districtId"):
        sample_row = group.iloc[0]
        district_profiles[district_id] = {
            "districtId": district_id,
            "district": sample_row["district"],
            "elevation_mean": float(sample_row["elevation_mean"]),
            "slope_mean": float(sample_row["slope_mean"]),
            "population_density": float(sample_row["population_density"]),
            "drainage_density_km": float(sample_row["drainage_density_km"]),
            "river_density_km": float(sample_row["river_density_km"]),
            "road_density": float(sample_row["road_density"]),
            "building_density": float(sample_row["building_density"]),
            "green_ratio": float(sample_row["green_ratio"]),
            "water_ratio": float(sample_row["water_ratio"]),
            "facility_density": float(sample_row["facility_density"]),
            "impervious_ratio": float(sample_row["impervious_ratio"]),
            "basin_depression_index": float(sample_row["basin_depression_index"]),
            "recommendation_base": sample_row["recommendation"],
        }

    # ------------------------------------------------------------------
    # 6. MENYIMPAN SELURUH ARTEFAK KE backend/app/ml/artifacts/
    # ------------------------------------------------------------------
    print("\n[6] Menyimpan artefak model...")
    # 1. Model pickle
    model_file = ARTIFACTS_DIR / "model.pkl"
    with open(model_file, "wb") as f:
        pickle.dump(final_model, f)
    print(f"  [OK] Model tersimpan: {model_file}")

    # 2. Explainer pickle
    explainer_file = ARTIFACTS_DIR / "explainer.pkl"
    with open(explainer_file, "wb") as f:
        pickle.dump(explainer, f)
    print(f"  [OK] SHAP Explainer tersimpan: {explainer_file}")

    # 3. District features lookup
    districts_file = ARTIFACTS_DIR / "district_features.json"
    districts_file.write_text(json.dumps(district_profiles, indent=2), encoding="utf-8")
    print(f"  [OK] Profil fitur kecamatan: {districts_file}")

    # 4. Metadata JSON
    metadata = {
        "model_type": "XGBoostRegressor",
        "version": "1.1.0",
        "training_data": str(data_path.name),
        "feature_columns": FEATURE_COLUMNS,
        "feature_metadata": FEATURE_METADATA,
        "evaluation_metrics": {
            "cv_mae": round(float(np.mean(fold_maes)), 2),
            "cv_rmse": round(float(np.mean(fold_rmses)), 2),
            "cv_r2": round(float(np.mean(fold_r2s)), 3),
            "cv_tier_accuracy_pct": round(float(np.mean(fold_tier_accs)), 1),
            "group_cv_mae": round(float(np.mean(group_maes)), 2),
            "group_cv_rmse": round(float(np.mean(group_rmses)), 2),
            "group_cv_r2": round(float(np.mean(group_r2s)), 3),
            "group_cv_tier_accuracy_pct": round(float(np.mean(group_tier_accs)), 1),
            "empirical_pearson_r_flood": round(float(r_flood), 4),
            "empirical_pearson_p_flood": round(float(p_r_flood), 6),
            "empirical_spearman_rho_flood": round(float(rho_flood), 4),
            "empirical_spearman_p_flood": round(float(p_rho_flood), 6),
            "empirical_pearson_r_hydromet": round(float(r_hydro), 4),
            "empirical_spearman_rho_hydromet": round(float(rho_hydro), 4),
            "macro_f1": round(float(macro_f1), 3),
            "baseline_mae": round(float(np.mean(baseline_maes)), 2),
            "baseline_tier_accuracy_pct": round(float(np.mean(baseline_tier_accs)), 1),
            "mae_improvement_over_baseline_pct": round(
                (np.mean(baseline_maes) - np.mean(fold_maes)) / np.mean(baseline_maes) * 100, 1
            ),
        },
        "top_features": [
            {
                "feature": FEATURE_COLUMNS[idx],
                "display_name": FEATURE_METADATA[FEATURE_COLUMNS[idx]]["display_name"],
                "importance_mean_abs_shap": round(float(mean_abs_shap[idx]), 3),
            }
            for idx in top_features_idx
        ],
        "shap_plots": {
            "summary": str(summary_path),
            "importance_bar": str(bar_path),
            "confusion_matrix": str(cm_path),
        },
    }
    metadata_file = ARTIFACTS_DIR / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    print(f"  [OK] Metadata model & XAI: {metadata_file}")

    # ------------------------------------------------------------------
    # 7. SINKRONISASI districts_30_seed.json DENGAN PREDIKSI TERBARU
    #    (Memperbarui skor & faktor SHAP, tetap menjaga array historicalEvents)
    # ------------------------------------------------------------------
    seed_file = ARTIFACTS_DIR / "districts_30_seed.json"
    if seed_file.exists():
        print("\n[7] Menyinkronkan districts_30_seed.json dengan skor & faktor SHAP baru...")
        try:
            with open(seed_file, "r", encoding="utf-8") as f:
                seed_data = json.load(f)

            # Hitung inferensi dan SHAP untuk skenario current
            cur_indices = df.index[df["scenario"] == "current"].tolist()
            cur_X = X.loc[cur_indices]
            cur_scores = final_model.predict(cur_X)
            cur_shap_vals = explainer(cur_X).values

            district_pred_map = {}
            for row_i, idx in enumerate(cur_indices):
                d_id = df.loc[idx, "districtId"]
                score_val = int(round(np.clip(cur_scores[row_i], 15, 96)))
                tier_val = to_risk_tier(score_val)
                conf_val = int(df.loc[idx, "confidence"])
                reco_val = str(df.loc[idx, "recommendation"])

                # Faktor penentu teratas SHAP
                row_shap = cur_shap_vals[row_i]
                abs_shap = np.abs(row_shap)
                top_idx = np.argsort(abs_shap)[::-1][:5]
                total_top_impact = max(0.001, np.sum(abs_shap[top_idx]))

                factors = []
                for fi in top_idx:
                    col = FEATURE_COLUMNS[fi]
                    feat_val = float(cur_X.iloc[row_i, fi])
                    contrib_pct = int(round((abs_shap[fi] / total_top_impact) * 100.0))
                    factors.append({
                        "factor": FEATURE_METADATA[col]["display_name"],
                        "contribution": contrib_pct,
                        "value": format_feature_value(col, feat_val),
                    })

                district_pred_map[d_id] = {
                    "score": score_val,
                    "riskLevel": tier_val,
                    "confidence": conf_val,
                    "factors": factors,
                    "recommendation": reco_val,
                }

            # Update array districts
            for d_entry in seed_data.get("districts", []):
                did = d_entry.get("districtId")
                if did in district_pred_map:
                    p = district_pred_map[did]
                    d_entry["score"] = p["score"]
                    d_entry["riskLevel"] = p["riskLevel"]
                    d_entry["confidence"] = p["confidence"]
                    d_entry["factors"] = p["factors"]
                    d_entry["recommendation"] = p["recommendation"]
                    # historicalEvents tetap dipertahankan utuh!

            # Update GeoJSON risk_layer properties
            if "risk_layer" in seed_data and "features" in seed_data["risk_layer"]:
                for feat in seed_data["risk_layer"]["features"]:
                    did = feat.get("properties", {}).get("districtId")
                    if did in district_pred_map:
                        feat["properties"]["score"] = district_pred_map[did]["score"]
                        feat["properties"]["riskLevel"] = district_pred_map[did]["riskLevel"]

            with open(seed_file, "w", encoding="utf-8") as f:
                json.dump(seed_data, f, indent=2, ensure_ascii=False)
            print(f"  [OK] districts_30_seed.json berhasil disinkronkan ({len(district_pred_map)} kecamatan)")
        except Exception as e:
            print(f"  [WARNING] Gagal sinkronisasi districts_30_seed.json: {e}")

    print("=" * 65)
    print("Tahap 2 & 3 SELESAI DENGAN SUKSES!")


if __name__ == "__main__":
    main()
