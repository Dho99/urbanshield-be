# Laporan Hasil Pelatihan Model Machine Learning & Explainable AI (SHAP)
## UrbanShield AI: Sistem Intelijen Geospasial untuk Prediksi Risiko Banjir Perkotaan

> **Pilot Wilayah:** Kota Bandung (30 Kecamatan)  
> **Model Algoritma:** XGBoost Regressor (140 Trees, Max Depth 3, LR 0.08)  
> **Explainability:** SHAP TreeExplainer (Lokal & Global Shapley Attribution)  
> **Dataset Training:** Fusi 5 Sumber Data Riil (OSM, Copernicus DEM GLO-30, ERA5 Reanalysis, BPS 2024, Diskar PB / BPBD 2025)  
> **Tanggal Retraining:** 14 Oktober 2026  
> **Status:** Siap Produksi / Serving Backend  

---

## 1. Ringkasan Eksekutif

Pelatihan ulang (*retraining*) model machine learning telah berhasil dilaksanakan secara end-to-end berbasis dataset riil lapangan terbaru:
1. **Fusi Data Riil:** Mengintegrasikan 26 fitur OpenStreetMap (OSM) dengan topografi riil satelit Copernicus DEM GLO-30 30m, presipitasi harian Copernicus / ECMWF ERA5 Reanalysis (2021–2023), kepadatan demografi resmi BPS Kota Bandung Dalam Angka 2024 (termasuk validasi Bojongloa Kaler ~39.510 jiwa/$km^2$), serta 160 titik kejadian bencana lapangan dari Open Data Diskar PB / BPBD Kota Bandung 2025 (46 titik banjir genangan dan 32 titik keruntuhan kirmir/tanggul drainase).
2. **Feature Engineering & Multi-Skenario:** Menghasilkan 14 fitur lingkungan terstandarisasi untuk 30 kecamatan di bawah 4 skenario kebencanaan (120 observasi pelatihan).
3. **Performa Validasi Silang (5-Fold CV):** Model XGBoost Regressor mencapai **Mean Absolute Error (MAE) 3.26 ± 0.93 poin** (pada skala 0–100), **RMSE 4.20 ± 1.46 poin**, **$R^2$ Score 0.834 (83.4%)**, dan **Akurasi Klasifikasi Tier Risiko 91.7%**.
4. **Peningkatan terhadap Baseline:** Memangkas galat MAE sebesar **63.1%** dibandingkan model pembanding `DummyRegressor` (mean baseline = 8.83 poin).
5. **Generalisasi Spasial (GroupKFold):** Mempertahankan **Akurasi Tier Spasial 80.0%** (MAE spasial 6.57 ± 1.77 poin) saat diuji pada 6 kecamatan yang sepenuhnya belum pernah dilihat model (*out-of-district holdout*).
6. **Validasi Empiris Eksternal:** Estimasi risiko model terbukti berkorelasi positif kuat dan signifikan secara statistik terhadap 46 titik kejadian banjir genangan riil Diskar PB 2025 (**Pearson $r$ = 0.5455, $p = 0.00182 < 0.01$**; **Spearman $\rho$ = 0.4427, $p = 0.0143 < 0.05$**).
7. **Explainability (XAI):** Modul **SHAP TreeExplainer** mengidentifikasi bahwa intensitas curah hujan ($\pm 4.49$ poin), elevasi dasar cekungan ($\pm 3.87$ poin), dan kapasitas efektif drainase ($\pm 2.00$ poin) mengendalikan lebih dari 65% total dinamika risiko banjir di Kota Bandung.

---

## 2. Struktur Data & Fitur Masukan (Tahap 1)

### A. Informasi Dataset Latihan
- **File Dataset Utama:** [`backend/ml_pipeline/data/training_dataset.csv`](file:///d:/Farid2/Project/urbansense-ai/backend/ml_pipeline/data/training_dataset.csv)
- **File Ground Truth Bencana:** [`backend/ml_pipeline/data/bandung_flood_ground_truth.csv`](file:///d:/Farid2/Project/urbansense-ai/backend/ml_pipeline/data/bandung_flood_ground_truth.csv)
- **Jumlah Sampel:** 120 baris ($30 \text{ Kecamatan} \times 4 \text{ Skenario}$)
- **Jumlah Kolom:** 27 kolom (14 fitur input, 3 komponen BNPB, 3 data bencana historis, 3 identitas wilayah, 4 atribut target & rekomendasi)

### B. Matriks 14 Fitur Input ($X$)

| No | Nama Kolom Fitur | Nama Tampilan (UI) | Kategori Kebencanaan | Satuan | Arah Pengaruh |
|:--:|---|---|---|---|:--:|
| 1 | `rainfall_mm` | Rainfall intensity | **Hazard** | mm / 24h | Positif (+) |
| 2 | `elevation_mean` | Topographic elevation | **Hazard** | m (mdpl) | Negatif (-) |
| 3 | `slope_mean` | Terrain slope | **Hazard** | Derajat (°) | Negatif (-) |
| 4 | `basin_depression_index` | Basin depression level | **Hazard** | Indeks (0-1) | Positif (+) |
| 5 | `river_density_km` | River network density | **Hazard** | km / km² | Positif (+) |
| 6 | `water_ratio` | Surface water ratio | **Hazard** | % | Positif (+) |
| 7 | `population_density` | Population density | **Vulnerability** | jiwa / km² | Positif (+) |
| 8 | `building_density` | Building density | **Vulnerability** | unit / km² | Positif (+) |
| 9 | `road_density` | Road network density | **Vulnerability** | km / km² | Positif (+) |
| 10 | `facility_density` | Critical facility density | **Vulnerability** | unit / km² | Positif (+) |
| 11 | `impervious_ratio` | Impervious surface ratio | **Vulnerability** | % | Positif (+) |
| 12 | `drainage_density_km` | Baseline drainage density | **Capacity** | km / km² | Negatif (-) |
| 13 | `effective_drainage_capacity` | Effective drainage capacity | **Capacity** | km / km² | Negatif (-) |
| 14 | `green_ratio` | Green infiltration area | **Capacity** | % | Negatif (-) |

---

## 3. Hasil Evaluasi Kinerja Model

### A. Validasi Silang 5-Fold Cross Validation (Fidelitas Formula)

| Lipatan (*Fold*) | Sampel Latih / Uji | MAE (Poin) | RMSE (Poin) | Koefisien Determinasi ($R^2$) | Akurasi Tier Risiko |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fold 1** | 96 / 24 | 4.41 | 5.35 | 0.821 | 83.3% |
| **Fold 2** | 96 / 24 | 4.27 | 6.47 | 0.670 | 95.8% |
| **Fold 3** | 96 / 24 | 2.04 | 2.56 | 0.928 | 100.0% |
| **Fold 4** | 96 / 24 | 3.02 | 3.34 | 0.847 | 87.5% |
| **Fold 5** | 96 / 24 | 2.57 | 3.31 | 0.902 | 91.7% |
| **RATA-RATA** | **120 Observasi** | **3.26 ± 0.93** | **4.20 ± 1.46** | **0.834 (83.4%)** | **91.7%** |

### B. Evaluasi Komparatif terhadap Baseline

| Model | Strategi Inferensi | MAE (Poin) | Akurasi Tier Risiko | Keterangan |
|---|---|:---:|:---:|---|
| **Baseline (DummyRegressor)** | Rata-rata global data latih | 8.83 | 72.5% | Titik rujukan performa dasar |
| **UrbanShield AI (XGBoost)** | GBDT dengan 14 fitur spasial | **3.26** | **91.7%** | **Peningkatan MAE 63.1%** |

### C. Validasi Spasial GroupKFold (Out-of-District Hold-out)

| Lipatan Spasial | Kecamatan Uji (*Hold-out*) | Spatial MAE | Spatial RMSE | Spatial $R^2$ | Akurasi Tier Spasial |
|:---:|---|:---:|:---:|:---:|:---:|
| **Spatial Fold 1** | Arcamanik, Babakan Ciparay, Bandung Kulon, Bojongloa Kaler, Coblong, Sukajadi | 8.21 | 11.51 | -0.645 | 79.2% |
| **Spatial Fold 2** | Antapani, Batununggal, Cidadap, Gedebage, Panyileukan, Ujung Berung | 5.32 | 6.91 | 0.539 | 83.3% |
| **Spatial Fold 3** | Bandung Kidul, Buah Batu, Cicendo, Cinambo, Lengkong, Sukasari | 9.10 | 10.03 | 0.350 | 58.3% |
| **Spatial Fold 4** | Andir, Bojongloa Kidul, Cibeunying Kidul, Cibiru, Kiaracondong, Mandalajati | 4.48 | 5.19 | 0.662 | 91.7% |
| **Spatial Fold 5** | Astana Anyar, Bandung Wetan, Cibeunying Kaler, Rancasari, Regol, Sumur Bandung | 5.73 | 6.73 | 0.229 | 87.5% |
| **RERATA SPASIAL** | **30 Kecamatan Terbagi Utuh** | **6.57 ± 1.77** | **8.07 ± 2.33** | **0.227** | **80.0%** |

### D. Validasi Empiris Eksternal terhadap 46 Titik Banjir Lapangan BPBD 2025

| Metrik Evaluasi Lapangan | Nilai | Signifikansi ($p$-Value) | Status Validasi |
|---|:---:|:---:|---|
| **Pearson Correlation ($r$) vs Banjir Diskar PB** | **0.5455** | **0.00182** | **Sangat Signifikan ($p < 0.01$)** |
| **Spearman Rank Correlation ($\rho$) vs Banjir Diskar PB** | **0.4427** | **0.01428** | **Signifikan Peringkat ($p < 0.05$)** |
| Pearson Correlation ($r$) vs Seluruh Bencana Hidromet | 0.3083 | 0.09738 | Korelasi Positif Moderat |
| Spearman Rank Correlation ($\rho$) vs Seluruh Bencana Hidromet | 0.2572 | 0.17000 | Korelasi Positif Moderat |

---

## 4. Analisis Explainable AI (SHAP TreeExplainer)

### Peringkat 5 Fitur Penentu Terbesar (Global SHAP Importance)
1. **Rainfall intensity (`rainfall_mm`):** Dampak rata-rata **$\pm 4.49$ poin** risiko (Positif / Pemicu eksternal utama).
2. **Topographic elevation (`elevation_mean`):** Dampak rata-rata **$\pm 3.87$ poin** risiko (Negatif / Dasar cekungan menerima limpasan).
3. **Effective drainage capacity (`effective_drainage_capacity`):** Dampak rata-rata **$\pm 2.00$ poin** risiko (Negatif / Saluran tersumbat menaikkan risiko).
4. **River network density (`river_density_km`):** Dampak rata-rata **$\pm 1.28$ poin** risiko (Positif / Proksimitas luapan alur sungai).
5. **Terrain slope (`slope_mean`):** Dampak rata-rata **$\pm 0.80$ poin** risiko (Negatif / Topografi datar memperlambat aliran air).

---

## 5. Status Artefak & Kesiapan Serving

Seluruh artefak serialisasi model telah diperbarui dan disinkronkan ke direktori backend:
1. `backend/app/ml/artifacts/model.pkl`: Model XGBoost terlatih.
2. `backend/app/ml/artifacts/explainer.pkl`: SHAP TreeExplainer terlatih.
3. `backend/app/ml/artifacts/district_features.json`: Profil fitur 30 kecamatan.
4. `backend/app/ml/artifacts/metadata.json`: Metadata dan metrik evaluasi lengkap.
5. `backend/app/ml/artifacts/districts_30_seed.json`: GeoJSON & array kecamatan tersinkronkan dengan skor dan faktor SHAP terbaru, serta mempertahankan array `historicalEvents` Diskar PB 2025.
6. `backend/tests/`: **14 dari 14 pengujian unit & integrasi lulus 100%**.
