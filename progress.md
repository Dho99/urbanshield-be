# UrbanShield AI — Progress & Implementation Roadmap

> **Judul Proyek:** Sistem Intelijen Geospasial Berbasis Explainable Machine Learning untuk Prediksi Risiko Banjir dan Prioritisasi Mitigasi Wilayah Perkotaan  
> **Pilot Wilayah:** Kota Bandung (30 Kecamatan)  
> **Target Pengguna:** Badan Penanggulangan Bencana Daerah (BPBD), Perencana Kota (Bappeda), Dinas Tata Ruang / PUPR, dan Masyarakat.

---

## 1. Ringkasan Status Proyek Saat Ini

Sistem ini dibangun dengan arsitektur monorepo yang memisahkan antara frontend visualisasi, backend API geospasial, dan modul data/ML:

```
┌────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                   │
│  /map (MapLibre GIS)  │  /prediction (SHAP Chart)      │
│  /dashboard (KPIs)    │  /recommendation (Prioritas)   │
└───────────────────────────▲────────────────────────────┘
                            │ REST API (JSON / GeoJSON)
┌───────────────────────────┴────────────────────────────┐
│                    Backend (FastAPI)                   │
│  Areas, RiskLayer, Predictions, Recommendations        │
└─────────────▲────────────────────────────▲─────────────┘
              │ PostGIS                    │ ML Inference (SHAP)
┌─────────────┴─────────────┐   ┌──────────┴─────────────┐
│    Database (PostgreSQL)  │   │  TUGAS ANDA:           │
│  kecamatan boundaries     │   │  • Feature Processing  │
│  OSM features, weather    │   │  • Model Training (XGB)│
│  risk predictions table   │   │  • SHAP Explainability │
└───────────────────────────┘   └────────────────────────┘
```

### Tabel Status Modul

| Modul / Komponen | Teknologi | Status Saat Ini | Keterangan |
|---|---|---|---|
| **Frontend UI** | Next.js 16.4, Tailwind 4, shadcn/ui | **Selesai (Siap Pakai)** | Dashboard, Peta GIS, Prediksi, Rekomendasi, Katalog Data |
| **Peta Choropleth** | MapLibre GL | **Selesai (Siap Pakai)** | Render GeoJSON 30 kecamatan dengan klasifikasi risiko |
| **Visualisasi XAI** | Recharts (Bar Chart Faktor) | **Selesai (Siap Pakai)** | Visualisasi kontribusi faktor SHAP (Why this score) |
| **Data Historis Bencana BPBD** | Integrasi 160 Titik Lapangan 2025 | **Selesai (Siap Pakai)** | Panel titik kejadian banjir & kerusakan fisik di bawah peta |
| **Backend REST API** | FastAPI, Pydantic, SQLAlchemy 2.0 | **Selesai (Siap Pakai)** | Endpoint `/areas`, `/map/risk-layer`, `/districts/{id}`, `/predictions` |
| **Database Spasial** | PostgreSQL 16 + PostGIS 3.4 | **Selesai (Siap Pakai)** | Migrasi Alembic & PostGIS Seeder (`scripts/seed.py`) |
| **Data Crawler OSM** | Overpass API, GeoPandas, Shapely | **Selesai (Data Siap)** | Menghasilkan `urban_osm_features_final.csv` (30 kecamatan × 26 fitur) |
| **Model ML Serving** | `backend/app/ml/` | **Perlu Dikerjakan (Anda)** | `artifacts/model.pkl` belum ada, masih fallback mock |
| **Data Processing & Training** | Python, Scikit-learn, XGBoost, SHAP | **Perlu Dikerjakan (Anda)** | Pipeline fusion data, feature engineering, training, dan XAI SHAP |

---

## 2. Analisis Audit Komponen yang Sudah Ada

### A. Frontend (`frontend/`)
Frontend sudah memiliki halaman dan alur interaksi yang sangat matang:
- **Dashboard (`/dashboard`)**: Metrik KPI (Total Wilayah, Wilayah Risiko Tinggi, Fasilitas Kritis Terpapar, Rata-rata Confidence).
- **Peta Risiko Spasial (`/map`)**: Peta interaktif MapLibre GL dengan layer batas poligon kecamatan, popup info, filter level risiko (*High, Medium, Low*), dan selektor skenario.
- **Prediksi Risiko & Explainability (`/prediction`)**: 
  - Form input pemilihan kecamatan dan skenario simulasi:
    1. `current` (Kondisi eksisting)
    2. `heavy_rain_24h` (Hujan lebat 24 jam)
    3. `heavy_rain_72h` (Hujan ekstrem berkepanjangan 72 jam)
    4. `drainage_failure` (Kegagalan / penyumbatan saluran drainase)
  - Skor risiko ($0 - 100$), confidence level, kartu rekomendasi otomatis.
  - Komponen **FactorChart**: Menampilkan dekomposisi faktor pengaruh berbasis Explainable AI (SHAP).
- **Rekomendasi Tindakan (`/recommendation`)**: Tabel prioritas aksi mitigasi struktural dan non-struktural.
- **Dukungan Dual-Mode**: Mendukung mode mock offline (`NEXT_PUBLIC_USE_MOCK=true`) dan mode API live backend (`NEXT_PUBLIC_USE_MOCK=false`).

### B. Backend (`backend/`)
- **Struktur API Modular**: Berada di `app/api/` (`areas.py`, `map.py`, `prediction.py`, `recommendation.py`, `datasets.py`, `auth.py`).
- **PostGIS Seeder (`scripts/seed.py`)**: Berfungsi memasukkan batas poligon kecamatan dari GeoJSON dan fitur OSM ke tabel PostgreSQL.
- **Kondisi ML Saat Ini**:
  - `backend/app/ml/model_loader.py` mencoba memuat `artifacts/model.pkl`. Jika file belum ada, ia mengembalikan `None`.
  - `backend/app/ml/predictor.py` saat ini masih menggunakan fallback perkalian skenario jika model belum ada.
  - `backend/app/ml/explainer.py` saat ini masih mengembalikan array faktor fallback statis.

### C. Aset Data yang Sudah Tersedia
Di folder `backend/urban_osm_crawler/output/`:
1. `kecamatan.geojson`: Batas poligon spasial 30 kecamatan Kota Bandung (WGS84 EPSG:4326).
2. `urban_osm_features_final.csv`: Data tabular 30 baris × 26 kolom fitur geospasial:
   - **Hidrologi**: `river_count`, `river_length_meter`, `drainage_count`, `drainage_length_meter`, `water_density`.
   - **Transportasi**: `road_count`, `road_length_meter`, `road_density`, `primary_road_length`, `secondary_road_length`.
   - **Fasilitas Kritis**: `hospital_count`, `clinic_count`, `school_count`, `university_count`, `government_count`, `public_facility_count`, `facility_density`.
   - **Bangunan & Tutupan Lahan**: `building_count`, `residential_count`, `commercial_count`, `building_density`, `green_area_m2`, `green_ratio`, `water_area_m2`, `water_ratio`.
3. `data_dictionary.csv`: Kamus data yang mendokumentasikan arti dari setiap kolom fitur.

---

## 3. Tugas Anda: Pengelolaan Data Processing & Model Training

Tugas utama Anda terbagi dalam 6 tahapan terstruktur dari hulu ke hilir:

```
[Tahap 1] Data Fusion & Enrichment (OSM + DEM Topografi + Cuaca + Demografi)
       │
       ▼
[Tahap 2] Feature Engineering & Pembuatan Skenario Simulasi (4 Skenario)
       │
       ▼
[Tahap 3] Model Training (XGBoost / LightGBM) & Evaluasi K-Fold CV
       │
       ▼
[Tahap 4] Explainable AI (SHAP TreeExplainer & Normalisasi Kontribusi Faktor)
       │
       ▼
[Tahap 5] Penyimpanan Artefak (model.pkl, scaler.pkl, metadata.json)
       │
       ▼
[Tahap 6] Integrasi ke Backend (Update predictor.py & explainer.py)
```

---

### Tahap 1: Pengayaan Data (Data Fusion & Enrichment)
Satuan unit analisis (data grain) adalah **tingkat Kecamatan (30 kecamatan)**. Agar model akurat dan realistis, gabungkan data OSM dengan faktor fisik banjir lainnya:

1. **Topografi / Elevasi (NASA DEM / SRTM Proxy)**:
   - Kota Bandung berbentuk cekungan (Bandung Basin). Wilayah selatan (Dayeuhkolot, Bandung Kidul, Bojongloa Kidul) berada pada elevasi rendah (~670 mdpl), sementara wilayah utara (Cidadap, Coblong) berada di elevasi tinggi (>750 mdpl).
   - Fitur yang ditambahkan:
     - `elevation_mean`: Rata-rata ketinggian wilayah (mdpl).
     - `slope_mean`: Rata-rata kemiringan lereng (derajat/persen).
2. **Karakteristik Cuaca / Curah Hujan (BMKG Proxy)**:
   - `rainfall_mm`: Curah hujan harian (mm/24 jam).
3. **Karakteristik Kerentanan Sosial (BPS Proxy)**:
   - `population_density`: Kepadatan penduduk per $km^2$.
4. **Target Label (Ground Truth $y$)**:
   - Bentuk skor target indeks risiko banjir kontinu ($0 - 100$) berdasarkan formula multi-kriteria kebencanaan:
     $$\text{Risk Score} = w_1 \cdot \text{Hazard} + w_2 \cdot \text{Vulnerability} - w_3 \cdot \text{Capacity}$$
     - **Hazard**: Intensitas hujan, densitas sungai, elevasi rendah (semakin rendah semakin rawan).
     - **Vulnerability**: Kepadatan penduduk, densitas bangunan, panjang jalan primer.
     - **Capacity**: Densitas saluran drainase, rasio ruang terbuka hijau (*green ratio*).

---

### Tahap 2: Feature Engineering & Dataset Simulasi Skenario
Frontend membutuhkan respon untuk 4 skenario. Oleh karena itu, siapkan dataset yang mencakup kondisi simulasi:

1. **Engineering Fitur Komposit**:
   - `impervious_ratio`: Rasio permukaan kedap air yang menghalangi infiltrasi air hujan (turunan dari `building_density` dan `road_density`).
   - `drainage_capacity_index`: Rasio panjang saluran drainase terhadap potensi limpasan air.
   - `retention_index`: Kapasitas retensi alami (`green_ratio` - `water_ratio`).
2. **Generasi Baris Skenario**:
   - Gandakan baris 30 kecamatan untuk 4 skenario simulasi:
     - `current`: Curah hujan normal (40–80 mm), kapasitas drainase normal (100%).
     - `heavy_rain_24h`: Curah hujan ekstrem 24 jam (130–160 mm).
     - `heavy_rain_72h`: Curah hujan ekstrem berkelanjutan (220–280 mm) dengan saturasi air tanah tinggi.
     - `drainage_failure`: Curah hujan sedang-tinggi, namun efisiensi drainase diturunkan hingga 40–50% (simulasi sedimentasi atau penyumbatan sampah).
   - Menghasilkan dataset latihan berukuran $30 \times 4 = 120$ observasi (atau 360 baris jika menggunakan 3 variasi histori tahunan).

---

### Tahap 3: Model Training & Evaluasi
1. **Pilihan Algoritma**:
   - Gunakan `XGBoostRegressor` atau `LGBMRegressor` (kompatibel penuh dengan SHAP TreeExplainer).
2. **Konfigurasi Training**:
   - Pisahkan fitur independen ($X$) dan target ($y$).
   - Simpan nama kolom fitur agar urutan input selalu konsisten.
   - Gunakan *K-Fold Cross Validation* (misal $k=5$) untuk memastikan model tidak overfitting.
   - Evaluasi metrik: **MAE** (Mean Absolute Error), **RMSE**, dan $R^2$ Score.
3. **Pemetaan Kategori Risiko**:
   - Output prediksi model ($0 - 100$) diklasifikasikan ke dalam 3 tier risiko sesuai frontend:
     - **Low (Rendah)**: Skor $< 40$
     - **Medium (Sedang)**: Skor $40 - 69$
     - **High (Tinggi)**: Skor $\ge 70$

---

### Tahap 4: Explainable AI Menggunakan SHAP
Fitur kunci dari proyek ini adalah **kemampuan menjelaskan alasan prediksi**:
1. Inisialisasi explainer: `explainer = shap.TreeExplainer(model)`.
2. Hitung SHAP Values untuk setiap sampel: `shap_values = explainer(X)`.
3. Format output penjelasan agar cocok dengan schema frontend:
   - Ambil 4–5 faktor teratas dengan nilai absolut kontribusi terbesar.
   - Normalisasikan nilai kontribusi ke persentase yang menjumlahkan ke $100\%$.
   - Tentukan arah pengaruh (`impact: "positive"` jika menaikkan risiko banjir, `"negative"` jika menurunkan risiko/memperbaiki kapasitas).
   - Sertakan nilai riil teramati (contoh: `"142 mm / 24h"`, `"0.8 km / km²"`, `"691 m"`).

---

### Tahap 5: Ekspor Artefak Model
Simpan hasil training ke direktori `backend/app/ml/artifacts/`:
1. `model.pkl`: Model XGBoost yang sudah dilatih (serialisasi pickle).
2. `metadata.json`: Berisi daftar urutan fitur (`feature_names`), parameter model, rentang nilai normalisasi, dan baseline metrik evaluasi.
3. `explainer.pkl` (opsional): Artefak SHAP explainer siap pakai.

---

### Tahap 6: Integrasi ke Backend Serving
Hubungkan artefak yang Anda buat ke backend:
1. Perbarui `backend/app/ml/predictor.py`:
   - Saat menerima request `districtId` dan `scenario`, ambil fitur kecamatan dari database atau dataframe fitur.
   - Modifikasi fitur sesuai skenario yang diminta.
   - Jalankan `score = model.predict(X_sample)[0]`.
   - Hitung confidence level berdasarkan deviasi estimasi model.
2. Perbarui `backend/app/ml/explainer.py`:
   - Hitung nilai SHAP lokal untuk sampel tersebut.
   - Kembalikan list `factors` yang langsung dikonsumsi oleh komponen chart di frontend.

---

## 4. Rencana Struktur Folder Pekerjaan Anda

Direkomendasikan membuat folder khusus `ml_pipeline/` di dalam backend agar rapi dan terisolasi dari kode serving:

```text
backend/
├── ml_pipeline/
│   ├── data/
│   │   ├── raw_osm_features.csv     (Salinan dari output crawler)
│   │   └── training_dataset.csv     (Dataset final setelah fusi dan skenario)
│   ├── 01_build_training_data.py    (Script fusi data OSM + DEM + Cuaca + Skenario)
│   ├── 02_train_model.py            (Script training XGBoost, evaluasi, & ekspor pkl)
│   ├── 03_evaluate_shap.py          (Script analisis XAI, summary plot, & validasi)
│   └── README.md                    (Dokumentasi metodologi ML)
│
└── app/
    └── ml/
        ├── artifacts/
        │   ├── model.pkl            <-- Dihasilkan dari Tahap 5
        │   └── metadata.json        <-- Dihasilkan dari Tahap 5
        ├── model_loader.py          (Memuat model.pkl saat server start)
        ├── predictor.py             (Melakukan inferensi fitur riil)
        └── explainer.py             (Menghasilkan kontribusi faktor SHAP)
```

---

## 5. Checklist Pelaksanaan Kerja (Action Checklist)

Gunakan checklist ini untuk memantau progres pengerjaan Anda:

- [x] **Persiapan Data (Tahap 1 - SELESAI)**
  - [x] Validasi 30 baris data di `urban_osm_features_final.csv`.
  - [x] Tambahkan atribut topografi (elevasi rata-rata & slope per kecamatan).
  - [x] Tambahkan atribut demografi (kepadatan penduduk).
  - [x] Rumuskan fungsi ground truth skor risiko banjir ($0 - 100$).
  - [x] Bangun dataset multi-skenario (Current, Heavy Rain 24h, Heavy Rain 72h, Drainage Failure).
  - [x] Simpan dataset akhir ke `backend/ml_pipeline/data/training_dataset.csv`.

- [x] **Pelatihan Model & Explainable AI (Tahap 2 & 3 - SELESAI)**
  - [x] Tulis script training menggunakan XGBoost Regressor (`backend/ml_pipeline/02_train_model.py`).
  - [x] Jalankan evaluasi 5-Fold Cross Validation (Hasil: MAE = 2.49 poin, RMSE = 3.32, R² = 0.917, Tier Accuracy = 94.2%).
  - [x] Integrasikan `shap.TreeExplainer` untuk mengekstrak kontribusi lokal tiap faktor.
  - [x] Buat fungsi pembentuk dictionary faktor penjelasan (persentase normalisasi & nilai riil berformat).
  - [x] Ekspor model ke `backend/app/ml/artifacts/model.pkl`, `explainer.pkl`, `district_features.json`, dan `metadata.json`.

- [x] **Integrasi Backend & Uji Coba (Tahap 4, 5, 6 - SELESAI)**
  - [x] Perbarui `backend/app/ml/model_loader.py` untuk memuat model, explainer, metadata, dan fitur profil kecamatan.
  - [x] Perbarui `backend/app/ml/predictor.py` agar membaca fitur riil 14 dimensi, menghitung nilai SHAP lokal, dan menjalankan `model.predict()`.
  - [x] Perbarui `backend/app/ml/explainer.py` agar menyajikan kontribusi SHAP asli yang dinamis.
  - [x] Uji coba unit test fungsi inferensi dan SHAP: Berhasil dieksekusi dengan akurat untuk berbagai kecamatan (Coblong, Gedebage) dan skenario.
  - [ ] Uji menyeluruh via UI frontend (`http://localhost:3005/prediction`) saat dev server dijalankan bersamaan.

---

## 6. Ringkasan Metrik Evaluasi Model (XGBoost Regressor)

Berikut adalah metrik performa model yang berhasil dilatih pada data Kota Bandung:

| Metrik Evaluasi | Nilai Hasil | Keterangan |
|---|---|---|
| **Mean Absolute Error (MAE)** | **2.49 poin** | Deviasi rata-rata prediksi hanya ~2.5 poin pada skala 0–100 |
| **Root Mean Squared Error (RMSE)** | **3.32 poin** | Akurasi sangat tinggi terhadap label target |
| **R² Score (Koefisien Determinasi)** | **0.917 (91.7%)** | Model mampu menjelaskan >91% variansi risiko banjir |
| **Tier Risk Accuracy** | **94.2%** | Ketepatan klasifikasi ke tier *Low*, *Medium*, dan *High* |

### Peringkat Faktor Pengaruh Terbesar (Global SHAP Feature Importance):
1. **Rainfall intensity (`rainfall_mm`)**: Pengaruh rata-rata $\pm 5.97$ poin risiko
2. **Elevation (`elevation_mean`)**: Pengaruh rata-rata $\pm 2.21$ poin risiko
3. **Effective drainage capacity (`effective_drainage_capacity`)**: Pengaruh rata-rata $\pm 1.26$ poin risiko
4. **Road network density (`road_density`)**: Pengaruh rata-rata $\pm 1.21$ poin risiko
5. **Population density (`population_density`)**: Pengaruh rata-rata $\pm 0.89$ poin risiko

- [x] **Integrasi Batas Administrasi Riil 30 Kecamatan (SELESAI)**
  - [x] Mengganti poligon grid kotak sintetis (*synthetic 6x5 fallback grid*) dengan poligon batas administratif resmi 30 kecamatan Kota Bandung (WGS84 EPSG:4326).
  - [x] Tiap kecamatan kini memiliki poligon batas asli berliku (misal: Batununggal 268 titik batas koordinat, Gedebage 892 titik, Coblong 1673 titik).
  - [x] Peta MapLibre GL diperbarui dengan garis batas administratif presisi dan highlight batas merah/putus-putus untuk kecamatan terpilih (sesuai standar tampilan Google Maps).
  - [x] Menambahkan *hover popup* interaktif yang menampilkan nama kecamatan, skor risiko, dan tingkat bahaya saat kursor digerakkan di atas peta.

---

*Dokumen ini dibuat otomatis sebagai panduan kerja tim data & machine learning UrbanShield AI.*
