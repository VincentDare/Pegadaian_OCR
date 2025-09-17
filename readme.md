# 📂 Pegadaian OCR & Clustering Dashboard

Aplikasi berbasis **Streamlit** untuk melakukan:
-  **OCR (Optical Character Recognition)** dari dokumen PDF Pegadaian (Daftar Kredit Jatuh Tempo & Kredit Bermasalah).
-  **Preprocessing & Postprocessing** data hasil OCR.
-  **Clustering nasabah** berdasarkan pinjaman dengan metode **KMeans**.
-  **Visualisasi hasil clustering** (bar chart, histogram, boxplot, pie chart).
-  Auto-cleanup output file setelah 30 menit (kecuali model `.pkl`).

ALUR MODEL
Dataset -> Preprocessing -> OCR -> PostProcessing -> Cleaning and Std -> Parser -> Clustering