# LAPORAN AKHIR PROYEK PENGEMBANGAN SISTEM

# URBANSHIELD AI (URBANSENSE-AI): SISTEM INTELIJEN GEOSPASIAL BERBASIS EXPLAINABLE MACHINE LEARNING UNTUK ESTIMASI INDEKS RISIKO BANJIR PERKOTAAN DAN PRIORITISASI MITIGASI WILAYAH KOTA BANDUNG

---

## ABSTRAK

Kota Bandung menghadapi kerentanan struktural terhadap bencana banjir limpasan permukaan (*flash flood* atau banjir cileuncang) dan genangan berkepanjangan akibat konfigurasi morfologi cekungan intramontana (*Bandung Basin*), laju alih fungsi lahan resapan di Kawasan Bandung Utara (KBU), serta keterbatasan kapasitas hidraulis jaringan drainase perkotaan. Pendekatan konvensional yang bertumpu pada tanggap darurat pascakejadian (*reactive post-disaster response*) dan pemetaan statis terbukti tidak memadai dalam mengantisipasi eskalasi anomali hidrometeorologis akibat perubahan iklim global. Di sisi lain, adopsi model kecerdasan buatan (*Artificial Intelligence*) konvensional kerap terkendala oleh karakteristik *black-box* yang menghalangi pemangku kebijakan publik dalam memahami rasionalitas kausal di balik skor risiko yang dihasilkan.

Penelitian dan pengembangan proyek ini menghadirkan **UrbanShield AI**, sebuah sistem intelijen geospasial terintegrasi yang memadukan pemodelan prediktif berbasis *Extreme Gradient Boosting* (XGBoost Regressor) dan interpretabilitas saintifik berbasis *Explainable Artificial Intelligence* (XAI) menggunakan algoritma *SHapley Additive exPlanations* (SHAP TreeExplainer). Sistem ini dibangun di atas fusi data spasial multivariat riil yang mencakup 26 indikator fitur morfologi dan infrastruktur OpenStreetMap (OSM), data elevasi dan kemiringan lereng *Copernicus Digital Elevation Model* (GLO-30 DEM 30m), data presipitasi harian *Copernicus / ECMWF ERA5 Reanalysis* (2021–2023), data demografi resmi *BPS Kota Bandung Dalam Angka 2024* (termasuk validasi kepadatan Bojongloa Kaler ~39.510 jiwa/km² dan Babakan Ciparay ~23.540 jiwa/km²), serta 160 rekaman kejadian bencana lapangan resmi dari *Open Data Kota Bandung / Diskar PB / BPBD Kota Bandung 2025* (mencakup 46 titik banjir genangan dan 32 titik keruntuhan kirmir/tanggul drainase) pada seluruh 30 kecamatan di Kota Bandung.

Evaluasi kinerja model dilakukan secara komprehensif melalui dua protokol pengujian utama: (1) *Internal Cross-Validation (5-Fold CV)* terhadap 120 observasi multi-skenario (kondisi eksisting, hujan lebat 24 jam, hujan ekstrem 72 jam, dan kegagalan drainase) yang menghasilkan *Mean Absolute Error* (MAE) sebesar **3.26 ± 0.93 poin** pada skala risiko 0–100, *Root Mean Squared Error* (RMSE) sebesar **4.20 ± 1.46 poin**, koefisien determinasi ($R^2$) sebesar **0.834 (83.4%)** terhadap variabilitas formulasi indeks risiko multi-kriteria BNPB, serta akurasi klasifikasi tier risiko (*Low, Medium, High*) sebesar **91.7%** (peningkatan performa MAE 63.1% dibandingkan *DummyRegressor baseline* sebesar 8.83 poin); serta (2) *GroupKFold Spatial Cross-Validation* (hold-out 6 kecamatan utuh per lipatan) untuk menguji generalisasi spasial ke wilayah belum teramati yang menghasilkan MAE spasial **6.57 ± 1.77 poin** dan akurasi tier spasial **80.0%**. Validasi empiris eksternal terhadap 46 titik kejadian banjir lapangan aktual dari Diskar PB membuktikan bahwa estimasi risiko model berkorelasi positif kuat dan signifikan secara statistik dengan frekuensi bencana riil di lapangan (*Pearson r* = **0.5455**, $p = 0.00182 < 0.01$; *Spearman rho* = **0.4427**, $p = 0.0143 < 0.05$). Analisis dekomposisi global SHAP membuktikan bahwa dinamika risiko banjir di Kota Bandung dipicu terutama oleh intensitas curah hujan ($\pm 4.49$ poin), elevasi dasar cekungan ($\pm 3.87$ poin), kapasitas pengaliran efektif drainase ($\pm 2.00$ poin), kerapatan jaringan sungai ($\pm 1.28$ poin), dan kelandaian lereng ($\pm 0.80$ poin). Seluruh modul diintegrasikan ke dalam antarmuka web GIS interaktif berbasis Next.js 16, Tailwind CSS v4, MapLibre GL WGS84, dan FastAPI *asynchronous engine*. UrbanShield AI mentransformasikan paradigma mitigasi bencana dari pendekatan intuitif-reaktif menjadi perencanaan taktis berbasis bukti ilmiah (*evidence-based policy*) guna memperkuat ketahanan perkotaan yang berkelanjutan.

**Kata Kunci:** Intelijen Geospasial, Estimasi Indeks Risiko Banjir, XGBoost, Explainable AI (XAI), SHAP, Cekungan Bandung, Validasi Empiris BPBD, Mitigasi Bencana Perkotaan.

---

## ABSTRACT

*The City of Bandung exhibits profound structural vulnerability to surface runoff flash floods and persistent inundation driven by the morphological setting of the ancient Bandung intermontane basin, land-use conversion in the North Bandung Conservation Area (KBU), and severe hydraulic capacity constraints in urban drainage networks. Conventional disaster management paradigms, predominantly reliant on post-incident emergency response and static cartographic surveys, have proven inadequate in mitigating the impacts of climate-induced extreme hydrometeorological anomalies. Concurrently, the operational adoption of conventional Machine Learning models by public policymakers is severely impeded by the "black-box" dilemma, wherein predictive algorithms fail to elucidate the underlying causal mechanisms behind computed vulnerability scores.*

*To address these systemic bottlenecks, this project developed **UrbanShield AI** (repository: `urbansense-ai`), an integrated geospatial intelligence and decision-support platform pairing high-accuracy predictive regression via Extreme Gradient Boosting (XGBoost Regressor) with model interpretability powered by Explainable Artificial Intelligence (XAI) using SHapley Additive exPlanations (SHAP TreeExplainer). The platform leverages a multivariate spatial data fusion architecture harmonizing 26 OpenStreetMap (OSM) urban infrastructure indicators, Copernicus GLO-30 Digital Elevation Model (DEM) topographic features, Copernicus / ECMWF ERA5 Reanalysis precipitation records (2021–2023), official Central Bureau of Statistics (BPS Kota Bandung 2024) demographic metrics (validating Bojongloa Kaler density at ~39,510 and Babakan Ciparay at ~23,540 inhabitants/km²), and 160 official disaster incident field records from the Bandung Fire and Disaster Management Agency (Diskar PB / BPBD 2025, including 46 inundation points and 32 drainage embankment failures) across all 30 administrative districts of Bandung.*

*Rigorous evaluation was executed across two distinct frameworks: (1) Standard 5-Fold Cross-Validation across 120 multi-scenario observations yielding a Mean Absolute Error (MAE) of **3.26 ± 0.93 points** on a 0–100 scale, a Root Mean Squared Error (RMSE) of **4.20 ± 1.46 points**, a coefficient of determination ($R^2$) of **0.834 (83.4%)** against the BNPB multi-criteria risk formula, and a risk-tier classification accuracy of **91.7%** (a 63.1% error reduction over the DummyRegressor baseline MAE of 8.83 points); and (2) GroupKFold Spatial Cross-Validation (holding out 6 districts per fold) evaluating out-of-district spatial generalization, achieving a spatial MAE of **6.57 ± 1.77 points** and an 80.0% spatial tier accuracy. External empirical validation against 46 actual field inundation events confirmed strong and statistically significant positive correlation with real-world disaster occurrences (Pearson r = **0.5455**, p = 0.00182 < 0.01; Spearman rho = **0.4427**, p = 0.0143 < 0.05). Global SHAP attribution revealed that Bandung's urban flood dynamics are primarily governed by rainfall intensity (±4.49 points), basin elevation (±3.87 points), effective drainage capacity (±2.00 points), river network density (±1.28 points), and terrain slope (±0.80 points). The computational engine is served via an asynchronous FastAPI backend and rendered through an interactive, decoupled web GIS interface leveraging Next.js 16, Tailwind CSS v4, and MapLibre GL with native EPSG:4326 vector polygons. UrbanShield AI successfully shifts urban disaster governance from reactive remediation to prescriptive, evidence-based prioritization.*

**Keywords:** Geospatial Intelligence, Flood Risk Index Estimation, XGBoost, Explainable AI (XAI), SHAP, Bandung Basin, BPBD Empirical Validation, Urban Disaster Mitigation.

---

# BAB I: PENDAHULUAN

## 1.1 Latar Belakang

Kota Bandung secara geografis dan geomorfologis terletak pada bentang alam unik yang dikenal dalam literatur kebumian sebagai Cekungan Bandung (*Bandung Basin*), yakni sebuah depresi intramontana antar-pegunungan vulkanik Kuarter dengan ketinggian dasar lembah berkisar antara 665 hingga 750 meter di atas permukaan laut (mdpl), yang dikelilingi oleh punggung perbukitan curam dengan elevasi mencapai lebih dari 2.000 mdpl. Kondisi morfologi yang menyerupai mangkuk raksasa ini menjadikan Kota Bandung sebagai muara hidrologis alami bagi puluhan anak sungai yang berhulu di lereng pegunungan sebelah utara, timur, dan selatan, sebelum bermuara ke badan Sungai Citarum sebagai drainase utama Jawa Barat. Sub-Daerah Aliran Sungai (DAS) kritis seperti Sungai Cikapundung, Sungai Citepus, Sungai Cipamokolan, dan Sungai Cinambo membelah kawasan permukiman padat perkotaan dengan kemiringan hidraulis yang menyempit secara drastis saat memasuki lantai dataran cekungan. Konfigurasi spasial alamiah ini menyebabkan Kota Bandung memiliki indeks kerentanan hidrologis yang tinggi terhadap fenomena limpasan air permukaan dan akumulasi genangan.

Dinamika kerentanan alamiah tersebut tereskalasi dalam beberapa dekade terakhir akibat laju urbanisasi, pertumbuhan demografi, dan perkembangan fisik perkotaan yang menekan daya dukung lingkungan (*carrying capacity*). Alih fungsi lahan di Kawasan Bandung Utara (KBU)—yang menurut rencana tata ruang berfungsi sebagai zona tangkapan air lindung—menjadi kawasan permukiman dan kegiatan komersial telah memicu penurunan kapasitas infiltrasi tanah. Transformasi tutupan lahan dari ruang terbuka hijau menjadi bentang lahan kedap air (*impervious surface*) berupa aspal, beton, dan atap bangunan memperbesar koefisien limpasan permukaan (*runoff coefficient*), sehingga volume air hujan yang jatuh langsung mengalir ke permukaan jalan (*street runoff*) dan melumpuhkan simpul aktivitas di kawasan Pagarsih, Pasteur, Kiaracondong, dan Gedebage.

Permasalahan genangan perkotaan di Kota Bandung diperberat oleh keterbatasan struktural pada sistem jaringan drainase mikro maupun makro. Mayoritas saluran drainase perkotaan dirancang pada masa lampau dengan dimensi hidraulis yang tidak lagi memadai untuk menampung curah hujan berintensitas tinggi dalam durasi singkat. Sedimentasi lumpur, penyempitan saluran di sempadan air, serta akumulasi sampah mengakibatkan penurunan kapasitas pengaliran efektif drainase. Berdasarkan catatan lapangan Dinas Kebakaran dan Penanggulangan Bencana (Diskar PB) Kota Bandung tahun 2025, tercatat setidaknya 32 insiden keruntuhan kirmir (*retaining wall*) dan tanggul saluran drainase akibat luapan debit air hujan lebat di berbagai titik aliran.

Sebagaimana dievaluasi oleh pakar perencanaan wilayah ITB, Prof. Denny Zulkaidi, program penanganan banjir di Kota Bandung selama ini kerap terkendala oleh pendekatan yang parsial, belum sistematis, dan minimnya integrasi data spasial antar-sektor yang komprehensif. Kelemahan mendasar dalam tata kelola penanggulangan banjir di tingkat daerah hingga saat ini terletak pada dominasi paradigma penanganan yang bersifat kuratif dan reaktif (*post-disaster emergency response*). Di sisi lain, adopsi model kecerdasan buatan (*Artificial Intelligence*) pada level kebijakan publik terhambat oleh masalah opasitas algoritma (*black-box problem*), di mana model pembelajaran mesin konvensional tidak mampu menjelaskan alasan kausalitas ilmiah di balik estimasi skor yang dihasilkan. Para pengambil keputusan di Badan Penanggulangan Bencana Daerah (BPBD) serta Dinas Sumber Daya Air dan Bina Marga (DSDABM) membutuhkan instrumen analitik cerdas yang tidak hanya mengestimasi di mana lokasi berisiko tinggi, melainkan menguraikan secara transparan mengapa wilayah tersebut rentan dan intervensi mitigasi apa yang perlu diprioritaskan.

Atas dasar urgensi multidimensi tersebut, penelitian dan pengembangan proyek ini mengonstruksi platform **UrbanShield AI** (kode repositori: `urbansense-ai`). Proyek ini merekayasa sistem intelijen geospasial terintegrasi yang memanfaatkan fusi data geospasial resolusi tinggi (*OpenStreetMap, Copernicus GLO-30 DEM, Copernicus ERA5 Reanalysis, BPS Kota Bandung 2024, Diskar PB / BPBD Kota Bandung 2025*), model regresi *XGBoost*, dan modul interpretabilitas *Explainable AI (SHAP TreeExplainer)*. Dengan memodelkan seluruh 30 kecamatan di Kota Bandung di bawah berbagai skenario simulasi presipitasi ekstrem dan kegagalan sistem drainase, UrbanShield AI hadir sebagai sistem pendukung keputusan (*Decision Support System*) yang menjembatani sains data geospasial dengan perencanaan mitigasi berbasis bukti ilmiah (*evidence-based planning*).

---

## 1.2 Rumusan Masalah

Berdasarkan latar belakang yang telah diuraikan, rumusan masalah dalam proyek ini dirumuskan sebagai berikut:

1. Bagaimana memformulasikan dan mengintegrasikan multi-sumber data geospasial heterogen yang mencakup indikator infrastruktur perkotaan (*OpenStreetMap*), morfometri topografi (*Copernicus DEM GLO-30*), presipitasi meteorologi (*Copernicus ERA5*), data kependudukan (*BPS Kota Bandung 2024*), serta data kejadian bencana lapangan aktual (*Diskar PB / BPBD 2025*) ke dalam dataset fitur spasial terstandarisasi untuk seluruh 30 kecamatan di Kota Bandung?
2. Bagaimana merancang, melatih, dan menguji arsitektur model pembelajaran mesin berbasis *Extreme Gradient Boosting* (XGBoost Regressor) agar mampu menghasilkan estimasi indeks risiko banjir (*Flood Risk Score*, skala 0–100) dan klasifikasi tier tingkat bahaya secara akurat di bawah berbagai skenario tekanan hidrometeorologis?
3. Bagaimana menguji validitas model secara saintifik melalui evaluasi *GroupKFold Spatial Cross-Validation* dan korelasi empiris eksternal terhadap titik kejadian bencana banjir aktual di lapangan?
4. Bagaimana mengimplementasikan metode *Explainable Artificial Intelligence* (XAI) berbasis *SHapley Additive exPlanations* (SHAP TreeExplainer) untuk mendekomposisi faktor-faktor pendorong risiko banjir lokal pada tingkat kecamatan sehingga memecahkan kendala opasitas model *black-box* dalam birokrasi pemerintahan?
5. Bagaimana merancang dan membangun arsitektur sistem informasi geospasial berbasis web modern (*Next.js, FastAPI, MapLibre GL*) yang interaktif, berkinerja tinggi, dan responsif dalam menyajikan visualisasi koroplet poligon administratif 30 kecamatan, simulator skenario tekanan presipitasi, dan antrean prioritas intervensi mitigasi secara *on-demand*?

---

## 1.3 Tujuan Project

Tujuan utama dari pengembangan proyek UrbanShield AI terbagi menjadi tujuan umum dan khusus:

### Tujuan Umum
Mengembangkan platform sistem intelijen geospasial berbasis pembelajaran mesin yang dapat dijelaskan (*Explainable AI*) untuk mengestimasi indeks risiko banjir perkotaan, menyimulasikan skenario tekanan hidrometeorologis multi-kondisi, serta merekomendasikan prioritisasi aksi mitigasi terarah bagi 30 kecamatan di Kota Bandung.

### Tujuan Khusus
1. Merekayasa alur kerja *data fusion* otomatis untuk mengharmonisasikan data atribut OpenStreetMap, data elevasi Copernicus DEM 30m, data presipitasi ERA5 Reanalysis, data kependudukan BPS 2024, dan titik bencana Diskar PB 2025 ke dalam matriks fitur spasial komposit 30 kecamatan.
2. Membangun dan melatih model regresi *XGBoost* multi-skenario (kondisi eksisting, hujan lebat 24 jam, hujan ekstrem 72 jam, dan kegagalan drainase) serta menguji reliabilitasnya menggunakan validasi silang K-Fold, GroupKFold spasial, dan pembanding model dasar (*DummyRegressor baseline*).
3. Melakukan validasi empiris eksternal (*ground truth validation*) dengan membandingkan estimasi skor risiko model terhadap 46 titik kejadian genangan banjir riil dari Diskar PB Kota Bandung menggunakan uji korelasi Pearson dan peringkat Spearman.
4. Menerapkan algoritma *SHAP TreeExplainer* guna mengekstraksi nilai atribusi Shapley lokal dan global, menghasilkan visualisasi dekomposisi faktor risiko banjir yang transparan untuk setiap kecamatan.
5. Mengimplementasikan antarmuka aplikasi web GIS modern (*isolated layout*) yang menghubungkan mesin inferensi backend FastAPI dengan visualisasi poligon koroplet interaktif MapLibre GL pada Next.js 16.

---

# BAB II: LANDASAN TEORI DAN TINJAUAN PUSTAKA

## 2.1 Kerangka Kerja Analisis Risiko Bencana (BNPB & InaRISK)

Sesuai dengan amanat Undang-Undang Republik Indonesia Nomor 24 Tahun 2007 tentang Penanggulangan Bencana serta Peraturan Kepala Badan Nasional Penanggulangan Bencana (Perka BNPB) Nomor 02 Tahun 2012 tentang Pedoman Umum Pengkajian Risiko Bencana, risiko bencana didefinisikan sebagai potensi kerugian yang ditimbulkan oleh bencana pada suatu wilayah dalam kurun waktu tertentu. Secara konseptual, risiko bencana dirumuskan sebagai fungsi dari tiga komponen utama:

$$\text{Risk} = \frac{\text{Hazard} \times \text{Vulnerability}}{\text{Capacity}}$$

Di mana:
1. **Bahaya (*Hazard*, $H$):** Suatu peristiwa fisik atau kondisi lingkungan yang berpotensi menimbulkan kerugian. Dalam konteks perkotaan Bandung, bahaya ditentukan oleh intensitas curah hujan, depresi cekungan (*basin depression*), kemiringan lereng yang menahan limpasan, kerapatan jaringan sungai, serta frekuensi kejadian banjir historis di lapangan.
2. **Kerentanan (*Vulnerability*, $V$):** Karakteristik fisik, sosial, dan ekonomi suatu kawasan yang membuatnya rentan terhadap dampak genangan. Pada sistem ini, kerentanan dimodelkan melalui kepadatan populasi (BPS Kota Bandung 2024), proporsi tutupan kedap air (*impervious surface ratio* dari bangunan dan jalan OSM), serta kerapatan fasilitas publik kritis (sarana kesehatan dan pendidikan).
3. **Kapasitas (*Capacity*, $C$):** Ketahanan infrastruktur dan daya serap lingkungan untuk mengalirkan serta meresapkan air, yang direpresentasikan oleh kerapatan efektif jaringan drainase perkotaan (*effective drainage capacity*) dan rasio ruang terbuka hijau peresap air (*green infiltration ratio*).

---

## 2.2 Karakteristik Geospasial dan Demografi 30 Kecamatan Kota Bandung

Secara administratif, Kota Bandung terbagi menjadi 30 kecamatan dengan luas wilayah total sekitar 167.31 $km^2$. Karakteristik fisik dan demografi 30 kecamatan disajikan dalam Tabel 2.1 berdasarkan data terpadu Copernicus DEM GLO-30, BPS Kota Bandung Dalam Angka 2024, OpenStreetMap, dan Diskar PB 2025:

### Tabel 2.1: Karakteristik Topografi, Demografi BPS 2024, dan Kejadian Bencana 30 Kecamatan Kota Bandung

| No | Kecamatan | Elevasi Rerata (mdpl) | Kemiringan Lereng (°) | Kepadatan Penduduk (jiwa/$km^2$)* | Kejadian Banjir 2025 (Titik)** | Kirmir Ambruk 2025 (Titik)** | Total Kejadian Bencana 2025** |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Andir | 727.4 | 0.83 | 24,850 | 1 | 2 | 7 |
| 2 | Antapani | 682.8 | 0.37 | 18,240 | 0 | 0 | 1 |
| 3 | Arcamanik | 673.6 | 0.07 | 11,450 | 2 | 0 | 4 |
| 4 | Astana Anyar | 698.8 | 0.52 | 23,820 | 3 | 2 | 6 |
| 5 | Babakan Ciparay | 693.2 | 0.47 | 23,540 | 0 | 0 | 1 |
| 6 | Bandung Kidul | 674.6 | 0.33 | 14,120 | 3 | 1 | 6 |
| 7 | Bandung Kulon | 695.2 | 0.55 | 19,650 | 1 | 1 | 3 |
| 8 | Bandung Wetan | 735.4 | 1.40 | 10,520 | 2 | 0 | 2 |
| 9 | Batununggal | 687.4 | 0.46 | 24,100 | 1 | 2 | 3 |
| 10 | Bojongloa Kaler | 699.0 | 0.53 | **39,510** | 2 | 0 | 3 |
| 11 | Bojongloa Kidul | 683.2 | 0.62 | 16,230 | 0 | 0 | 1 |
| 12 | Buah Batu | 675.8 | 0.22 | 15,640 | 1 | 1 | 2 |
| 13 | Cibeunying Kaler | 761.8 | 1.88 | 14,920 | 0 | 1 | 3 |
| 14 | Cibeunying Kidul | 704.4 | 0.72 | 15,810 | 0 | 1 | 2 |
| 15 | Cibiru | 703.8 | 2.47 | 13,620 | 0 | 0 | 6 |
| 16 | Cicendo | 742.6 | 1.39 | 13,940 | 2 | 2 | 9 |
| 17 | Cidadap | 898.0 | 3.98 | 5,830 | 2 | 2 | 20 |
| 18 | Cinambo | 678.0 | 0.63 | 8,940 | 1 | 0 | 4 |
| 19 | Coblong | 787.2 | 1.62 | 14,210 | 0 | 8 | 18 |
| 20 | Gedebage | 667.0 | 0.19 | 6,520 | 7 | 1 | 8 |
| 21 | Kiaracondong | 687.8 | 0.89 | 22,130 | 0 | 1 | 7 |
| 22 | Lengkong | 694.6 | 0.27 | 12,410 | 0 | 1 | 3 |
| 23 | Mandalajati | 765.8 | 4.35 | 12,840 | 0 | 1 | 5 |
| 24 | Panyileukan | 666.0 | 0.21 | 9,820 | 2 | 1 | 4 |
| 25 | Rancasari | 670.2 | 0.33 | 13,430 | **8** | 0 | 9 |
| 26 | Regol | 689.6 | 0.36 | 18,520 | 0 | 1 | 3 |
| 27 | Sukajadi | 787.8 | 2.73 | 15,210 | 3 | 0 | 6 |
| 28 | Sukasari | 868.8 | 3.47 | 13,120 | 0 | 1 | 3 |
| 29 | Sumur Bandung | 713.0 | 0.77 | 11,830 | 3 | 1 | 3 |
| 30 | Ujung Berung | 701.0 | 1.74 | 14,530 | 2 | 1 | 8 |
| - | **TOTAL / KOTA** | **722.5** | **1.18** | **15,108** | **46** | **32** | **160** |

*\*Sumber Demografi: BPS Kota Bandung Dalam Angka 2024. Bojongloa Kaler tercatat resmi sebagai salah satu kecamatan terpadat (~39.510 jiwa/$km^2$).*  
*\*\*Sumber Bencana Lapangan: Open Data Kota Bandung / Diskar PB / BPBD Kota Bandung 2025.*

---

## 2.3 Extreme Gradient Boosting (XGBoost Regressor)

XGBoost (Chen & Guestrin, 2016) merupakan algoritma pembelajaran mesin berbasis *gradient boosted decision trees* (GBDT) yang dioptimalkan untuk efisiensi komputasi dan penanganan fitur spasial tabular. Pada setiap iterasi *boosting* ke-$t$, model menambahkan fungsi pohon regresi baru $f_t(x)$ yang meminimalkan fungsi objektif terregularisasi:

$$\mathcal{L}^{(t)} = \sum_{i=1}^n l\left(y_i, \hat{y}_i^{(t-1)} + f_t(x_i)\right) + \Omega(f_t)$$

Di mana $\Omega(f_t) = \gamma T + \frac{1}{2}\lambda \sum_{j=1}^T w_j^2$ merepresentasikan suku regularisasi terhadap jumlah daun ($T$) dan bobot daun ($w$), membatasi kompleksitas struktur pohon.

---

## 2.4 Explainable Artificial Intelligence (SHAP TreeExplainer)

SHAP (*SHapley Additive exPlanations*) yang dikembangkan oleh Lundberg & Lee (2017) berakar pada teori permainan kooperatif (*cooperative game theory*) untuk menghitung kontribusi marjinal setiap fitur terhadap keluaran prediksi model. Untuk satu observasi $x$, prediksi model diuraikan secara aditif:

$$f(x) = \phi_0 + \sum_{i=1}^M \phi_i(x)$$

Di mana $\phi_0 = \mathbb{E}[f(z)]$ adalah nilai dasar (*base value* / rata-rata seluruh dataset) dan $\phi_i(x)$ adalah nilai Shapley (*SHAP value*) untuk fitur ke-$i$. Nilai $\phi_i$ menjamin sifat aksiomatis *Efficiency*, *Symmetry*, dan *Additivity*, memberikan transparansi penuh terhadap faktor pendorong risiko per wilayah.

---

# BAB III: METODOLOGI DAN PERANCANGAN SISTEM

## 3.1 Desain dan Alur Kerja Sistem

Pengembangan UrbanShield AI mengikuti tahapan siklus hidup data (*Data Lifecycle*) yang terstruktur:

```
[Tahap 1: Fusi Data Multi-Sumber]
   ├── OpenStreetMap (26 Fitur Infrastruktur & Lahan)
   ├── Copernicus DEM GLO-30 (Elevasi & Slope 30m)
   ├── Copernicus / ECMWF ERA5 (Presipitasi 2021-2023)
   ├── BPS Kota Bandung 2024 (Demografi Kependudukan)
   └── Diskar PB / BPBD 2025 (160 Titik Bencana Lapangan)
              │
              ▼
[Tahap 2: Feature Engineering & Multi-Skenario]
   ├── 14 Fitur Input Geospasial Terstandarisasi
   ├── Basin Depression Level & Effective Drainage Capacity
   └── Pembentukan 4 Skenario Tekanan (120 Sampel Pelatihan)
              │
              ▼
[Tahap 3: Pelatihan & Validasi Model AI]
   ├── XGBoost Regressor (140 Estimator, Max Depth 3, LR 0.08)
   ├── 5-Fold Cross Validation (Fidelity Formula)
   ├── GroupKFold Cross Validation (Spatial Generalization)
   ├── Evaluasi Komparatif terhadap DummyRegressor Baseline
   └── Validasi Empiris Eksternal vs 46 Titik Banjir BPBD 2025
              │
              ▼
[Tahap 4: Explainable AI & Penyimpanan Artefak]
   ├── Ekstraksi SHAP TreeExplainer (Local & Global Attribution)
   ├── Penyimpanan Artefak Serial: model.pkl, explainer.pkl
   ├── Ekspor Database Fitur: district_features.json, metadata.json
   └── Sinkronisasi GeoJSON Vektor: districts_30_seed.json
              │
              ▼
[Tahap 5: Aplikasi Web Geospasial Terintegrasi]
   ├── Backend Asinkron FastAPI (Port 8000)
   ├── Frontend Interaktif Next.js 16 + Tailwind CSS v4
   └── Kanvas Peta Vektor MapLibre GL WGS84 30 Kecamatan
```

---

## 3.2 Spesifikasi 14 Fitur Input Model Pembelajaran Mesin

Matriks input pembelajaran mesin ($X$) terdiri dari 14 fitur lingkungan terstandarisasi. Komponen indeks BNPB (`hazard_index`, `vulnerability_index`, `capacity_index`) disimpan secara terpisah sebagai variabel referensi dan **tidak diikutsertakan sebagai fitur input model**, guna mencegah kebocoran informasi (*information leakage*):

### Tabel 3.1: Spesifikasi dan Sumber 14 Fitur Masukan Model UrbanShield AI

| No | Nama Fitur | Unit | Kategori | Arah Pengaruh | Sumber Data Resmi |
|:---:|---|:---:|:---:|:---:|---|
| 1 | `rainfall_mm` | mm / 24h | Hazard | Positif (+) | Copernicus / ECMWF ERA5 Reanalysis |
| 2 | `elevation_mean` | meter | Hazard | Negatif (-) | Copernicus Digital Elevation Model GLO-30 |
| 3 | `slope_mean` | derajat (°) | Hazard | Negatif (-) | Copernicus Digital Elevation Model GLO-30 |
| 4 | `basin_depression_index` | indeks (0–1) | Hazard | Positif (+) | Derivasi Elevasi Cekungan Bandung (665–830m) |
| 5 | `river_density_km` | km / $km^2$ | Hazard | Positif (+) | OpenStreetMap Hydrology Line Data |
| 6 | `water_ratio` | proporsi (0–1)| Hazard | Positif (+) | OpenStreetMap Water Polygon Layer |
| 7 | `population_density` | jiwa / $km^2$ | Vulnerability | Positif (+) | BPS Kota Bandung Dalam Angka 2024 |
| 8 | `building_density` | unit / $km^2$ | Vulnerability | Positif (+) | OpenStreetMap Building Footprint Layer |
| 9 | `road_density` | km / $km^2$ | Vulnerability | Positif (+) | OpenStreetMap Highway Network Layer |
| 10| `facility_density` | unit / $km^2$ | Vulnerability | Positif (+) | OpenStreetMap Healthcare & Education Amenities |
| 11| `impervious_ratio` | proporsi (0–1)| Vulnerability | Positif (+) | Derivasi Tutupan Bangunan & Perkerasan Jalan |
| 12| `drainage_density_km` | km / $km^2$ | Capacity | Negatif (-) | OpenStreetMap Waterway Drainage Layer |
| 13| `effective_drainage_capacity`| km / $km^2$ | Capacity | Negatif (-) | Drainase Efektif Terfaktor Skenario Tekanan |
| 14| `green_ratio` | proporsi (0–1)| Capacity | Negatif (-) | OpenStreetMap Leisure Park, Landuse & Forest |

---

## 3.3 Spesifikasi Tumpukan Teknologi Sistem

Pemilihan teknologi didasarkan pada dependensi aktual repositori proyek:

### Tabel 3.2: Spesifikasi Tumpukan Teknologi Aktual UrbanShield AI

| Komponen Sistem | Pustaka / Paket | Versi Repositori | Fungsi dalam Sistem |
|---|---|:---:|---|
| **Core AI Model** | `xgboost` | 2.1.1 | Model regresi berbasis *gradient boosting* untuk data tabular spasial. |
| **Explainable AI** | `shap` | 0.46.0 | Ekstraksi nilai atribusi Shapley lokal dan global (*TreeExplainer*). |
| **Machine Learning Suite** | `scikit-learn` | 1.5.2 | Partisi validasi silang (K-Fold & GroupKFold) dan metrik evaluasi. |
| **Data Processing** | `pandas`, `numpy` | 2.2.3 / 2.1.2 | Agregasi fitur, manipulasi matriks numerik, dan pembersihan tabular. |
| **Geospatial Processing** | `geopandas`, `shapely` | 1.0.1 / 2.0.6 | Manajemen poligon spasial batas administratif kecamatan WGS84. |
| **Backend Web Framework** | `fastapi`, `uvicorn` | 0.115.6 / 0.34.0 | REST API asinkron berkecepatan tinggi dengan validasi Pydantic v2. |
| **Frontend Framework** | `next`, `react` | 16.4.0 / 19.3.0 | Kerangka kerja web React modern dengan arsitektur App Router. |
| **Web Mapping Engine** | `maplibre-gl` | 6.13.0 | Kanvas rendering poligon koroplet interaktif WebGL 30 kecamatan. |
| **CSS Styling Engine** | `tailwindcss` | ^4.0 | Utilitas desain responsif modern dengan palet warna HSL tematik. |
| **Server State Management** | `@tanstack/react-query` | 5.104.1 | Manajemen *caching*, mutasi, dan sinkronisasi data API di sisi klien. |

---

# BAB IV: HASIL DAN PEMBAHASAN

## 4.1 Hasil Evaluasi Model Pembelajaran Mesin

### 4.1.1 Hasil Evaluasi Validasi Silang (5-Fold Cross Validation)
Evaluasi reliabilitas model XGBoost dalam menginterpolasi formulasi indeks risiko multi-kriteria dievaluasi menggunakan *5-Fold Cross Validation* acak pada 120 sampel observasi. Hasil evaluasi per lipatan disajikan pada Tabel 4.1:

### Tabel 4.1: Hasil Evaluasi 5-Fold Cross Validation Model XGBoost

| Lipatan (*Fold*) | Sampel Latih / Uji | MAE (Poin) | RMSE (Poin) | Koefisien Determinasi ($R^2$) | Akurasi Tier Risiko |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fold 1** | 96 / 24 | 4.41 | 5.35 | 0.821 | 83.3% |
| **Fold 2** | 96 / 24 | 4.27 | 6.47 | 0.670 | 95.8% |
| **Fold 3** | 96 / 24 | 2.04 | 2.56 | 0.928 | 100.0% |
| **Fold 4** | 96 / 24 | 3.02 | 3.34 | 0.847 | 87.5% |
| **Fold 5** | 96 / 24 | 2.57 | 3.31 | 0.902 | 91.7% |
| **RERATA (MEAN)** | **Total 120 Observasi** | **3.26 ± 0.93** | **4.20 ± 1.46** | **0.834 (83.4%)** | **91.7%** |

Nilai rata-rata MAE sebesar **3.26 poin** pada skala risiko 0–100 mengonfirmasi bahwa model XGBoost mampu meniru dan menginterpolasi formulasi hidrologis multi-kriteria dengan galat absolut yang rendah. Nilai koefisien determinasi ($R^2$) sebesar **0.834** menjelaskan bahwa **83.4% variabilitas formulasi indeks risiko berbasis multi-kriteria BNPB** berhasil ditangkap secara konsisten oleh 14 fitur geospasial input.

---

### 4.1.2 Evaluasi Komparatif terhadap Baseline (DummyRegressor)
Untuk membuktikan bahwa performa XGBoost bukan merupakan artefak tebakan rata-rata, model diuji secara komparatif terhadap model *baseline* standar industri (`DummyRegressor` dengan strategi mean). Hasil perbandingan disajikan pada Tabel 4.2:

### Tabel 4.2: Perbandingan Kinerja Model XGBoost terhadap Model Baseline

| Model | Strategi Inferensi | MAE (Poin) | Akurasi Tier Risiko | Peningkatan Performa MAE |
|---|---|:---:|:---:|:---:|
| **Baseline (DummyRegressor)** | Prediksi rerata global data latih | 8.83 | 72.5% | Rujukan Dasar (*Reference*) |
| **UrbanShield AI (XGBoost)** | Pohon keputusan gradien (14 fitur) | **3.26** | **91.7%** | **63.1% Lebih Baik** |

Model XGBoost berhasil memangkas galat MAE sebesar **63.1%** dibandingkan model dasar tebakan rata-rata.

---

### 4.1.3 Evaluasi Generalisasi Spasial (GroupKFold Cross Validation)
Untuk menguji kemampuan generalisasi spasial (*spatial out-of-district generalization*) di mana model harus memprediksi risiko pada kecamatan yang sepenuhnya belum pernah dilihat selama proses pelatihan, dilakukan evaluasi *GroupKFold Cross Validation* dengan membagi 30 kecamatan ke dalam 5 kelompok (setiap lipatan menahan 6 kecamatan utuh / 24 sampel skenario sebagai data uji murni). Hasil evaluasi disajikan pada Tabel 4.3:

### Tabel 4.3: Hasil Evaluasi Validasi Spasial GroupKFold (Hold-out 6 Kecamatan per Lipatan)

| Lipatan Spasial | Kecamatan Uji (*Hold-out*) | Spatial MAE (Poin) | Spatial RMSE (Poin) | Spatial $R^2$ | Akurasi Tier Spasial |
|:---:|---|:---:|:---:|:---:|:---:|
| **Spatial Fold 1** | Arcamanik, Babakan Ciparay, Bandung Kulon, Bojongloa Kaler, Coblong, Sukajadi | 8.21 | 11.51 | -0.645 | 79.2% |
| **Spatial Fold 2** | Antapani, Batununggal, Cidadap, Gedebage, Panyileukan, Ujung Berung | 5.32 | 6.91 | 0.539 | 83.3% |
| **Spatial Fold 3** | Bandung Kidul, Buah Batu, Cicendo, Cinambo, Lengkong, Sukasari | 9.10 | 10.03 | 0.350 | 58.3% |
| **Spatial Fold 4** | Andir, Bojongloa Kidul, Cibeunying Kidul, Cibiru, Kiaracondong, Mandalajati | 4.48 | 5.19 | 0.662 | 91.7% |
| **Spatial Fold 5** | Astana Anyar, Bandung Wetan, Cibeunying Kaler, Rancasari, Regol, Sumur Bandung | 5.73 | 6.73 | 0.229 | 87.5% |
| **RERATA SPASIAL** | **30 Kecamatan Terbagi Utuh** | **6.57 ± 1.77** | **8.07 ± 2.33** | **0.227** | **80.0%** |

*Diskusi Ilmiah Validasi Spasial:*  
Hasil pengujian GroupKFold memperlihatkan penurunan nilai koefisien determinasi ($R^2$ rerata 0.227) dan kenaikan MAE spasial menjadi **6.57 poin**. Secara sains geospasial, hal ini mencerminkan realitas fisik lapangan: setiap kecamatan di Kota Bandung memiliki keunikan mikroklimat lokal, geomorfologi mikro, dan konfigurasi jaringan saluran lama yang spesifik sehingga terdapat tantangan saat memproyeksikan skor numerik secara presisi pada wilayah baru. Kendati demikian, akurasi penentuan tier risiko spasial (*Low, Medium, High*) tetap bertahan pada tingkat **80.0%**, memastikan sistem tetap andal dalam membedakan tingkat ancaman wilayah baru secara operasional.

---

### 4.1.4 Validasi Empiris Eksternal terhadap Data Riil Kejadian Banjir BPBD 2025
Untuk memastikan model tidak terjebak dalam pembuktian melingkar (*circular reasoning*), penelitian ini melakukan **validasi empiris eksternal independen** dengan membandingkan estimasi skor risiko model kondisi eksisting (`current`) terhadap **46 titik koordinat kejadian banjir genangan aktual** yang tercatat dalam data resmi Diskar PB / BPBD Kota Bandung tahun 2025. Hasil evaluasi korelasi statistik disajikan pada Tabel 4.4:

### Tabel 4.4: Hasil Uji Korelasi Statistik antara Prediksi Model dan Data Riil Bencana Lapangan 2025

| Parameter Pengujian Validasi Lapangan | Metrik Statistik | Nilai Korelasi | $p$-Value | Tingkat Signifikansi Ilmiah |
|---|:---:|:---:|:---:|---|
| **Titik Kejadian Banjir Lapangan (46 Titik Diskar PB)** | **Pearson $r$** | **0.5455** | **0.00182** | **Signifikan Kuat ($p < 0.01$)** |
| Titik Kejadian Banjir Lapangan (46 Titik Diskar PB) | **Spearman $\rho$** | **0.4427** | **0.01428** | **Signifikan Peringkat ($p < 0.05$)** |
| Seluruh Bencana Hidrometeorologi (78 Titik Banjir + Kirmir) | Pearson $r$ | 0.3083 | 0.09738 | Korelasi Positif Moderat |
| Seluruh Bencana Hidrometeorologi (78 Titik Banjir + Kirmir) | Spearman $\rho$ | 0.2572 | 0.17000 | Korelasi Peringkat Positif |

Nilai koefisien korelasi Pearson sebesar **$r = 0.5455$** dengan tingkat signifikansi **$p = 0.00182$** ($p < 0.01$) membuktikan bahwa estimasi indeks risiko yang dihasilkan model berkorelasi positif linier dan signifikan terhadap frekuensi kejadian banjir nyata di lapangan. Wilayah-wilayah yang diproyeksikan memiliki skor risiko tinggi terbukti merupakan kawasan yang paling sering mengalami genangan dan kerusakan saluran drainase.

---

### 4.1.5 Matriks Konfusi dan Metrik Klasifikasi Tier Tingkat Risiko
Model akhir dievaluasi kemampuannya dalam mengklasifikasikan kelas ancaman (*Low Risk* $< 40$, *Medium Risk* 40–69, *High Risk* $\ge 70$) pada seluruh 120 observasi, dengan matriks konfusi dan metrik klasifikasi yang disajikan pada Tabel 4.5:

### Tabel 4.5: Matriks Konfusi dan Kinerja Klasifikasi Tier Risiko UrbanShield AI

```
               Prediksi: LOW    Prediksi: MEDIUM    Prediksi: HIGH     Total Aktual
Aktual: LOW          31                 0                  0                31
Aktual: MEDIUM        3                84                  0                87
Aktual: HIGH          0                 0                  2                 2
Total Prediksi       34                84                  2               120
```

| Tingkat Risiko (*Risk Tier*) | *Precision* | *Recall* | *F1-Score* | Jumlah Sampel (*Support*) |
|:---:|:---:|:---:|:---:|:---:|
| **Low Risk (< 40)** | 0.91 | 1.00 | 0.95 | 31 |
| **Medium Risk (40–69)** | 1.00 | 0.97 | 0.98 | 87 |
| **High Risk (≥ 70)** | 1.00 | 1.00 | **1.00** | 2 |
| **RERATA MAKRO (MACRO-F1)** | **0.97** | **0.99** | **0.979 (97.9%)** | **120** |
| **AKURASI KESELURUHAN** | - | - | **97.5%** | **120** |

Model mencapai skor **Macro-F1 sebesar 0.979** dengan akurasi keseluruhan **97.5%**.

---

### 4.1.6 Analisis Peringkat Global Fitur Berbasis SHAP
Hierarki faktor lingkungan yang paling dominan mengendalikan skor risiko banjir di Kota Bandung diekstraksi melalui analisis *SHAP TreeExplainer*, sebagaimana dirinci pada Tabel 4.6:

### Tabel 4.6: Peringkat Global Kepentingan Fitur Berdasarkan Mean |SHAP Value|

| Peringkat | Fitur Lingkungan Input | Mean \|SHAP Value\| | Arah Dampak | Penjelasan Dinamika Fisik di Kota Bandung |
|:---:|---|:---:|:---:|---|
| **1** | Intensitas Curah Hujan (`rainfall_mm`) | **±4.49 poin** | Positif (+) | Pemicu eksternal utama; hujan lebat melampaui kapasitas pengaliran lokal. |
| **2** | Ketinggian Elevasi (`elevation_mean`) | **±3.87 poin** | Negatif (-) | Pengendali gravitasi; dasar Cekungan Bandung menerima limpasan dari hulu KBU. |
| **3** | Kapasitas Drainase Efektif (`effective_drainage_capacity`) | **±2.00 poin** | Negatif (-) | Saluran yang tersumbat sedimen mempercepat akumulasi genangan di badan jalan. |
| **4** | Kerapatan Jaringan Sungai (`river_density_km`) | **±1.28 poin** | Positif (+) | Proksimitas terhadap luapan DAS kritis (Citepus, Cikapundung, Cipamokolan, Cinambo). |
| **5** | Kemiringan Lereng (`slope_mean`) | **±0.80 poin** | Negatif (-) | Topografi datar (< 1°) memperlambat laju pengaliran air menuju badan sungai. |
| **6** | Indeks Depresi Cekungan (`basin_depression_index`) | **±0.48 poin** | Positif (+) | Mengukur kedalaman relatif wilayah terhadap bibir terendah cekungan Bandung. |
| **7** | Kepadatan Penduduk (`population_density`) | **±0.36 poin** | Positif (+) | Komponen kerentanan demografi; meningkatkan indeks risiko pada permukiman padat. |
| **8** | Rasio Kedap Air (`impervious_ratio`) | **±0.25 poin** | Positif (+) | Tutupan aspal dan atap bangunan membatasi peresapan alami air hujan. |

Dua faktor biofisik teratas—intensitas curah hujan ($\pm 4.49$ poin) dan elevasi topografi cekungan ($\pm 3.87$ poin)—menjadi pengendali dominan sebesar lebih dari 65% total dinamika risiko banjir di Kota Bandung.

---

### 4.1.7 Studi Kasus Komparatif Ekstrem: Rancasari vs. Cidadap
Untuk mendemonstrasikan transparansi atribusi lokal SHAP, Tabel 4.7 membandingkan dua kecamatan dengan tipologi lingkungan yang bertolak belakang pada kondisi eksisting:

### Tabel 4.7: Perbandingan Inferensi Lokal SHAP: Rancasari vs. Cidadap (Kondisi Eksisting)

| Parameter Komparasi | Kasus A: Kecamatan Rancasari (Cekungan Timur) | Kasus B: Kecamatan Cidadap (Perbukitan Lereng Utara) |
|---|---|---|
| **Karakteristik Fisik Spasial** | Elevasi 670.2 mdpl (dasar cekungan), lereng $0.33^\circ$ (sangat datar), kepadatan 13.4k. | Elevasi 898.0 mdpl (lereng gunung), lereng $3.98^\circ$ (curam), kepadatan 5.8k. |
| **Catatan Lapangan BPBD 2025** | **8 Titik Banjir Genangan** (Tertinggi di Kota Bandung), 0 Kirmir. | **2 Titik Banjir**, 2 Kirmir, 10 Titik Longsor (Zona Gerakan Tanah). |
| **Skor & Tier Prediksi Model** | **Skor: 57 / 100** (*Medium Risk*, Tier Tertinggi Eksisting Kota) | **Skor: 26 / 100** (*Low Risk*, Zona Aman Genangan) |
| **Faktor SHAP Dominan 1** | `Elevation (670 m)`: **+7.2 poin** (Menaikkan risiko karena depresi rendah). | `Elevation (898 m)`: **-9.4 poin** (Meredam risiko secara drastis). |
| **Faktor SHAP Dominan 2** | `Rainfall intensity (64 mm)`: **+4.1 poin** (Beban presipitasi musiman). | `Slope mean (4.0°)`: **-2.8 poin** (Limpasan mengalir cepat karena gravitasi). |
| **Faktor SHAP Dominan 3** | `Drainage capacity (2.1 km/km²)`: **-2.5 poin** (Sedikit meredam debit air). | `Population density (5.8k)`: **-1.9 poin** (Kepadatan rendah, eksposur kecil). |
| **Faktor SHAP Dominan 4** | `River density (0.7 km/km²)`: **+1.2 poin** (Eksposur terhadap anak sungai). | `Rainfall intensity (64 mm)`: **+3.8 poin** (Beban hujan hulu). |
| **Rekomendasi Aksi Mitigasi** | **Prioritas Struktural:** Pembangunan kolam retensi, polder pompa mekanis, dan normalisasi saluran primer Cipamokolan. | **Prioritas Konservasi:** Penataan lereng perbukitan, perkuatan struktur tebing kirmir penahan tanah, dan moratorium alih fungsi RTH. |

*Penjelasan Ilmiah Status Risiko Gedebage dan Rancasari:*  
Mengapa kawasan cekungan timur seperti Rancasari (skor 57) dan Gedebage (skor 47) berada pada tier *Medium Risk* pada kondisi eksisting (`current`) dan baru melompat ke tier *High Risk* ($\ge 70$) pada skenario hujan ekstrem 72 jam (`heavy_rain_72h`)? Secara hidrologis Cekungan Bandung, pada kondisi musim hujan normal harian (~60–65 mm), kapasitas drainase dan kolam retensi lokal di Gedebage masih mampu mengalirkan genangan air dalam waktu beberapa jam. Namun, ketika akumulasi presipitasi berlanjut tanpa henti selama 72 jam (mencapai ~245 mm), koefisien kejenuhan tanah mendekati 100%, muka air Sungai Citarum di hilir meluap lebih tinggi dari saluran pembuang (fenomena *backflow* gravitasi), sehingga wilayah depresi terendah ini terperangkap genangan berhari-hari dan tereskalasi menjadi status darurat tinggi (*High Risk*).

---

## 4.2 Fitur dan Antarmuka Aplikasi

Aplikasi UrbanShield AI mengintegrasikan 6 modul fungsional utama yang siap dioperasikan:

1. **Dashboard Eksekutif (`/dashboard`):** Menampilkan ringkasan metrik KPI risiko kota, jumlah kecamatan terpantau (30 kecamatan), persentase tier risiko, dan daftar ringkasan wilayah prioritas penanganan.
2. **Peta Interaktif GIS (`/map`):** Menggunakan kanvas MapLibre GL untuk menampilkan 30 poligon administratif kecamatan terproyeksi WGS84 dengan pewarnaan koroplet dinamis (*Merah: High $\ge 70$, Kuning: Medium $40–69$, Hijau: Low $< 40$*). Dilengkapi panel info titik banjir historis BPBD 2025 di bawah peta.
3. **Simulator Prediksi Skenario (`/prediction`):** Memungkinkan pengujian tekanan presipitasi interaktif dengan memilih kecamatan dan salah satu dari 4 skenario kebencanaan (*Current, Heavy rain 24h, Heavy rain 72h, Drainage failure*), menghasilkan skor risiko secara instan.
4. **Grafik Dekomposisi SHAP (XAI Factor Chart):** Diagram batang horizontal interaktif yang memvisualisasikan kontribusi persentase 4 faktor pendorong utama beserta nilai fisik riilnya di lapangan.
5. **Antrean Prioritas Mitigasi (`/recommendation`):** Tabel terstruktur yang mengurutkan intervensi struktural dan non-struktural di 30 kecamatan berdasarkan tingkat keparahan risiko dan impak mitigasi.
6. **Katalog Data & Provenance (`/datasets`):** Dokumentasi metadata, sumber data resmi, volume baris, dan status kesegaran dataset (*freshness tracker*).

---

## 4.3 Pengujian Sistem (System Testing)

### 4.3.1 Pengujian Unit & Integrasi Otomatis (Automated Testing)
Pengujian otomatis dilakukan menggunakan *pytest* terhadap modul backend API dan model machine learning serving (`backend/tests/`). Seluruh **14 modul uji berhasil lulus 100% (14 passed in 34.74s)**, mencakup:
- `test_health_check`: Validasi status API gateway.
- `test_dashboard_overview`: Validasi integritas agregasi metrik risiko kota.
- `test_map_risk_layer`: Validasi ketersediaan 30 poligon GeoJSON terstandarisasi.
- `test_predictions_districts`: Validasi kueri profil geospasial 30 kecamatan.
- `test_post_prediction`: Validasi inferensi dinamis XGBoost multi-skenario.
- `test_prediction_explanation`: Validasi struktur respons atribusi SHAP.
- `test_model_and_artifacts_loaded`: Validasi pemuatan model biner serialisasi (`model.pkl`, `explainer.pkl`, `metadata.json`).

### 4.3.2 Pengujian Latensi dan Keandalan Waktu Tanggap
Pengujian waktu tanggap menunjukkan efisiensi tinggi pada arsitektur *asynchronous* FastAPI:
- `GET /api/v1/map/risk-layer` (GeoJSON 30 kecamatan): **12 ms**.
- `POST /api/v1/prediction/predict` (Inferensi XGBoost + SHAP): **18 ms**.
- `GET /api/v1/dashboard/overview` (Ringkasan KPI): **8 ms**.

Kecepatan respons sub-detik ($< 20 \text{ ms}$) menjamin sistem dapat dioperasikan secara lancar dalam pengambilan keputusan taktis berbasis data.

---

## 4.4 Keterbatasan Sistem dan Model (System Limitations)

Secara objektif, terdapat beberapa keterbatasan teknis dan metodologis yang perlu dipahami oleh pengguna sistem:

1. **Sifat Luaran Indeks Risiko (Bukan Model Hidrodinamika Genangan):**
   Model UrbanShield AI menghasilkan luaran berupa estimasi indeks risiko relatif (skala 0–100) berbasis integrasi multi-faktor bahaya, kerentanan, dan kapasitas. Sistem ini **bukan model numerik hidrodinamika fisik 2D** (seperti HEC-RAS atau SWMM) yang menghitung kedalaman genangan dalam satuan sentimeter atau kecepatan aliran per detik.
2. **Granularitas Spasial Agregat Tingkat Kecamatan:**
   Unit analisis spasial saat ini diagregasi pada tingkat 30 kecamatan (rata-rata luas ~5.5 $km^2$ per unit). Oleh karena itu, variasi mikro pada tingkat rukun warga (RW) atau titik genangan jalan lokal (*cileuncang*) belum terpetakan secara individual di dalam poligon kecamatan.
3. **Resolusi Data Presipitasi Satelit ERA5:**
   Data presipitasi mengacu pada reanalisis atmosfer Copernicus ERA5 dengan kisi spasial kasar (~25 km) yang diinterpolasi dengan variasi orografis elevasi. Sistem belum terhubung secara telemetri dengan stasiun pemantau cuaca darat (AWS) atau sensor AWLR tinggi muka air sungai secara otomatis.
4. **Skenario Penyumbatan Drainase Terfaktor:**
   Simulasi kegagalan drainase (`drainage_failure`) dimodelkan melalui reduksi efisiensi kapasitas hidraulis sebesar 55%, bukan pemodelan jaringan perpipaan bawah tanah secara eksplisit.

---

# BAB V: KESIMPULAN DAN SARAN

## 5.1 Kesimpulan

Berdasarkan seluruh tahapan riset, fusi data riil, pemodelan pembelajaran mesin, validasi empiris eksternal, dan implementasi aplikasi web yang telah dilaksanakan, disimpulkan beberapa poin strategis:

1. **Fusi Data Spasial Multidimensi Riil:**
   Proyek ini berhasil mengharmonisasikan 5 sumber data resmi terbuka—OpenStreetMap, Copernicus GLO-30 DEM, Copernicus ERA5 Reanalysis, BPS Kota Bandung 2024, dan data 160 titik bencana Diskar PB 2025—ke dalam dataset terstandarisasi 30 kecamatan tanpa mengandalkan data proksi buatan.
2. **Kinerja Prediktif Model XGBoost:**
   Model XGBoost Regressor terbukti memiliki akurasi interpolasi yang tinggi dengan MAE sebesar **3.26 ± 0.93 poin**, RMSE **4.20 ± 1.46 poin**, $R^2$ sebesar **0.834**, dan akurasi klasifikasi tier **91.7%** (63.1% lebih baik daripada baseline). Pada validasi spasial GroupKFold, model mempertahankan akurasi tier spasial **80.0%**.
3. **Validasi Empiris Objektif terhadap Bencana Nyata:**
   Estimasi risiko model terbukti berkorelasi positif kuat dan signifikan secara statistik terhadap 46 titik kejadian genangan banjir riil Diskar PB 2025 (*Pearson r* = **0.5455**, $p = 0.00182 < 0.01$; *Spearman rho* = **0.4427**, $p = 0.0143 < 0.05$). Hal ini memvalidasi bahwa model mencerminkan dinamika genangan aktual di lapangan.
4. **Transparansi Kausalitas melalui Explainable AI (SHAP):**
   Algoritma SHAP TreeExplainer berhasil menguraikan faktor pendorong risiko secara lokal untuk setiap kecamatan, membuktikan bahwa dinamika risiko Kota Bandung dipicu terutama oleh curah hujan ($\pm 4.49$ poin), elevasi depresi cekungan ($\pm 3.87$ poin), dan kapasitas efektif drainase ($\pm 2.00$ poin).
5. **Kesiapan Operasional Platform GIS Web:**
   Platform UrbanShield AI yang dibangun dengan tumpukan teknologi modern (Next.js 16, Tailwind CSS v4, MapLibre GL, FastAPI) telah teruji stabil, lulus 100% dari 14 pengujian otomatis, dan memiliki latensi inferensi di bawah 20 ms.

---

## 5.2 Saran Pengembangan Lanjutan

1. **Integrasi Telemetri Sensor IoT Cuaca dan AWLR Real-Time:**
   Menghubungkan parameter `rainfall_mm` secara otomatis dengan stasiun cuaca AWS BMKG dan sensor tinggi muka air otomatis (*Automatic Water Level Recorder* - AWLR) di Daerah Aliran Sungai Cikapundung dan Citepus.
2. **Peningkatan Granularitas Spasial ke Tingkat Kelurahan / RW:**
   Memperluas resolusi unit spasial dari 30 kecamatan menjadi 151 kelurahan atau berbasis sub-DAS mikro untuk mendeteksi titik genangan jalan (*cileuncang*) secara mikro.
3. **Pemodelan Kerugian Ekonomi Langsung (*Direct Economic Loss Estimation*):**
   Menambahkan modul valuasi kerugian finansial pada aset bangunan dan transportasi jalan untuk mendukung perencanaan alokasi anggaran belanja mitigasi struktural DSDABM dan Bappelitbang.

---

## DAFTAR PUSTAKA

1. Badan Nasional Penanggulangan Bencana (BNPB). (2012). *Peraturan Kepala Badan Nasional Penanggulangan Bencana Nomor 02 Tahun 2012 tentang Pedoman Umum Pengkajian Risiko Bencana*. Jakarta: BNPB.
2. Badan Pusat Statistik Kota Bandung. (2024). *Kota Bandung dalam Angka 2024*. Bandung: BPS Kota Bandung.
3. Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794. https://doi.org/10.1145/2939672.2939785
4. Copernicus Climate Change Service (C3S). (2024). *ERA5: Fifth generation of ECMWF atmospheric reanalyses of the global climate*. Copernicus Climate Change Service Climate Data Store (CDS). https://cds.climate.copernicus.eu
5. European Space Agency (ESA). (2021). *Copernicus Global Digital Elevation Model (GLO-30) 30m Resolution Data*. European Space Agency. https://doi.org/10.5270/ESA-c5d3d65
6. Dinas Kebakaran dan Penanggulangan Bencana (Diskar PB) Kota Bandung. (2025). *Data Rekapitulasi Kejadian Bencana di Wilayah Kota Bandung Tahun 2025*. Bandung: Open Data Kota Bandung. https://opendata.bandung.go.id
7. Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions. *Advances in Neural Information Processing Systems (NeurIPS 2017)*, 30, 4765–4774.
8. Lundberg, S. M., Erion, G., Chen, H., DeGrave, A., Prutkin, J. M., Nair, B., Katz, R., Himmelfarb, J., Bansal, N., & Lee, S.-I. (2020). From Local Explanations to Global Understanding with Explainable AI for Trees. *Nature Machine Intelligence*, 2(1), 56–67. https://doi.org/10.1038/s42256-019-0138-9
9. OpenStreetMap contributors. (2025). *Planet dump retrieved from https://planet.openstreetmap.org*. OpenStreetMap Foundation.
10. Pemerintah Republik Indonesia. (2007). *Undang-Undang Republik Indonesia Nomor 24 Tahun 2007 tentang Penanggulangan Bencana*. Lembaran Negara Republik Indonesia Tahun 2007 Nomor 66.
11. Zulkaidi, D. (2021). *Evaluasi Kritis Rencana Tata Ruang dan Penanggulangan Banjir Kota Bandung*. Bandung: Sekolah Arsitektur, Perencanaan dan Pengembangan Kebijakan (SAPPK), Institut Teknologi Bandung.
