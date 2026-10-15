# UrbanSense AI — Machine Learning Pipeline

Modul ini bertanggung jawab atas seluruh siklus *data preparation*, pelatihan model prediksi risiko banjir, evaluasi kinerja model terhadap baseline, dan interpretasi model menggunakan SHAP (Explainable AI).

---

## Notebook Analisis Interaktif

Untuk melihat proses secara langsung di Jupyter/VS Code, buka:

`ml_pipeline/urban_flood_risk_analysis.ipynb`

Notebook tersebut menyajikan:

- **Business understanding**: latar belakang, tujuan bisnis, pertanyaan analitik, keputusan yang didukung, dan keterbatasan.
- **Data understanding dan data quality check**: ukuran dataset, tipe data, missing values, duplikasi, statistik deskriptif, serta rentang target.
- **EDA**: distribusi `risk_score`, perbandingan empat skenario, kecamatan dengan risiko tertinggi, korelasi fitur, dan scatter plot fitur utama.
- **Pemodelan dan evaluasi internal**: 5-fold cross-validation XGBoost dibandingkan `DummyRegressor` baseline.
- **Interpretasi**: panduan merangkum insight dan hubungan ke evaluasi SHAP yang sudah tersedia pada script pipeline.

Notebook membaca `data/training_dataset_v2.csv` jika tersedia, lalu menggunakan `data/training_dataset.csv` sebagai fallback. Notebook tidak mengubah dataset atau artefak model.

Dependensi notebook: `numpy`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn`, dan opsional `xgboost`. Jika `xgboost` belum tersedia, bagian EDA tetap dapat dijalankan dan bagian evaluasi model akan dilewati dengan pesan yang jelas.

---

## Urutan Eksekusi Pipeline (Pipeline Execution Flow)

Untuk mereproduksi dataset dan model dari awal:

### 1. Pengambilan Data Riil Cuaca & Elevasi (Data Acquisition)
```bash
python ml_pipeline/fetch_bandung_data.py
```
- **Fungsi**: Mengambil data curah hujan harian 2021–2023 dari Copernicus ERA5 Reanalysis dan elevasi/lereng dari Open-Meteo Elevation API untuk 30 kecamatan Kota Bandung.
- **Output**: Tersimpan di folder `ml_pipeline/data_raw/`.

---

### 2. Pembangunan & Integrasi Dataset Pelatihan
```bash
python ml_pipeline/01_build_training_data.py
python ml_pipeline/01b_integrate_real_data.py
```
- **Fungsi**:
  - `01_build_training_data.py`: Menggabungkan fitur fisik dari OpenStreetMap (OSM) dan membentuk 4 skenario iklim.
  - `01b_integrate_real_data.py`: Mengintegrasikan data riil ERA5 dan DEM topografi ke dalam dataset.
- **Output**: `ml_pipeline/data/training_dataset.csv` (120 observasi × 16 fitur).

---

### 3. Pelatihan & Evaluasi Model XGBoost
```bash
python ml_pipeline/02_train_model.py --input ml_pipeline/data/training_dataset.csv
```
- **Fungsi**:
  - Melatih model `XGBoostRegressor` dengan 5-fold cross-validation.
  - Membandingkan metrik kuantitatif terhadap `DummyRegressor (Mean)` baseline.
  - Menyimpan artefak model terlatih ke `app/ml/artifacts/`:
    - `model.pkl` (Model XGBoost)
    - `explainer.pkl` (SHAP TreeExplainer)
    - `metadata.json` (Skema fitur dan ringkasan metrik)
    - `district_features.json` & `districts_30_seed.json` (Data baseline inferensi)

---

### 4. Evaluasi Mendalam XAI & Pembuatan Plot SHAP
```bash
python ml_pipeline/03_evaluate_shap.py
```
- **Fungsi**:
  - Menghitung nilai Shapley marjinal untuk seluruh observasi.
  - Menghasilkan visualisasi interpretasi global dan kurva dependensi.
  - Menganalisis studi kasus mikro untuk 5 kecamatan representatif (Gedebage, Coblong, Babakan Ciparay, Cidadap, Arcamanik).
- **Output**: Tersimpan di `ml_pipeline/results/`:
  - `shap_summary.png`
  - `shap_importance.png`
  - `shap_dependence_rainfall_mm.png`
  - `shap_dependence_elevation_mean.png`
  - `shap_dependence_effective_drainage_capacity.png`
  - `confusion_matrix.png`
  - `shap_evaluation_summary.json`

---

## Struktur Folder

```
ml_pipeline/
├── data/                      # Dataset pelatihan (training_dataset.csv)
├── data_raw/                  # Data mentah ERA5 dan DEM Open-Meteo
├── results/                   # Grafik visualisasi evaluasi & SHAP
├── legacy/                    # Arsip script eksperimen lama
├── fetch_bandung_data.py      # Pengambilan data cuaca & elevasi
├── 01_build_training_data.py  # Ekstraksi fitur fisik OSM
├── 01b_integrate_real_data.py # Integrasi data riil
├── 02_train_model.py          # Training model & baseline comparison
└── 03_evaluate_shap.py        # Evaluasi mendalam SHAP
```
