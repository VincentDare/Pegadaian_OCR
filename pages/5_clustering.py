import streamlit as st
import os, glob, pandas as pd
from PIL import Image

OUTPUT_DIR = "output"

st.title("📊 Clustering & Visualisasi")

# Cari file clustering yang ada (prioritas: clustered_data > predicted_clusters)
possible_files = [
    os.path.join(OUTPUT_DIR, "clustering", "model", "clustered_data.csv"),
    os.path.join(OUTPUT_DIR, "clustering", "model", "predicted_clusters.csv")
]
clustered_file = None
for f in possible_files:
    if os.path.exists(f):
        clustered_file = f
        break

summary_dir = os.path.join(OUTPUT_DIR, "clustering", "summary")
vis_dir = os.path.join(OUTPUT_DIR, "clustering", "visualization")

# Helper function untuk ambil file terbaru
def get_latest_file(directory, pattern):
    try:
        files = glob.glob(os.path.join(directory, pattern))
        return max(files, key=os.path.getctime) if files else None
    except Exception:
        return None

# Cek apakah ada hasil clustering
if clustered_file is None or not os.path.exists(clustered_file):
    st.warning("⚠️ Belum ada hasil clustering. Silakan jalankan pipeline terlebih dahulu.")
    st.info("Jalankan pipeline melalui halaman 'Pipeline' atau jalankan `python pipeline.py` di terminal.")
    st.stop()

# Load data
clustered_df = pd.read_csv(clustered_file)

# === SECTION 1: STATISTIK CEPAT ===
st.header("📈 Statistik Cepat")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Nasabah", f"{len(clustered_df):,}")

with col2:
    total_pinjaman = clustered_df['UANG_PINJAMAN'].sum()
    st.metric("Total Pinjaman", f"Rp {total_pinjaman:,.0f}")

with col3:
    avg_pinjaman = clustered_df['UANG_PINJAMAN'].mean()
    st.metric("Rata-rata Pinjaman", f"Rp {avg_pinjaman:,.0f}")

with col4:
    n_clusters = clustered_df['CLUSTER'].nunique()
    st.metric("Jumlah Segmen", n_clusters)

st.divider()

# === SECTION 2: DATA LENGKAP ===
st.header("📋 Data Lengkap Clustering")

with st.expander("📂 Lihat Data Clustering Lengkap", expanded=False):
    st.dataframe(clustered_df, use_container_width=True, height=400)
    
    # Download button untuk data lengkap
    csv_full = clustered_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="⬇️ Download Data Clustering Lengkap",
        data=csv_full,
        file_name="clustered_data_full.csv",
        mime="text/csv",
        use_container_width=True
    )

st.divider()

# === SECTION 3: VISUALISASI UTAMA (4 CHART - 2x2 GRID) ===
st.header("📊 Visualisasi Segmen - Ringkasan")
st.markdown("*Grafik sederhana untuk memahami distribusi nasabah dan pinjaman*")

# 4 chart utama dalam grid 2x2
main_charts = [
    ("Distribusi Nasabah (Pie Chart)", "cluster_pie_*.png", 
     "Persentase nasabah di setiap segmen"),
    ("Jumlah Nasabah per Segmen", "cluster_count_bar_*.png",
     "Total nasabah di setiap segmen"),
    ("Rata-rata Pinjaman per Segmen", "cluster_bar_*.png",
     "Rata-rata uang pinjaman per segmen"),
    ("Distribusi Pinjaman (Boxplot)", "cluster_boxplot_*.png",
     "Sebaran pinjaman per segmen"),
]

chart_found = False

# Baris 1 (Chart 1 & 2)
cols_row1 = st.columns(2)
for idx in range(2):
    if idx < len(main_charts):
        title, pattern, description = main_charts[idx]
        chart_file = get_latest_file(vis_dir, pattern)
        
        with cols_row1[idx]:
            if chart_file and os.path.exists(chart_file):
                st.subheader(title)
                st.caption(description)
                try:
                    img = Image.open(chart_file)
                    st.image(img, use_container_width=True)
                    chart_found = True
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.info(f"ℹ️ {title} belum tersedia")

# Baris 2 (Chart 3 & 4)
cols_row2 = st.columns(2)
for idx in range(2, 4):
    if idx < len(main_charts):
        title, pattern, description = main_charts[idx]
        chart_file = get_latest_file(vis_dir, pattern)
        
        with cols_row2[idx - 2]:
            if chart_file and os.path.exists(chart_file):
                st.subheader(title)
                st.caption(description)
                try:
                    img = Image.open(chart_file)
                    st.image(img, use_container_width=True)
                    chart_found = True
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.info(f"ℹ️ {title} belum tersedia")

if not chart_found:
    st.warning("⚠️ Tidak ada visualisasi yang ditemukan. Pastikan pipeline sudah dijalankan sampai tahap visualisasi.")

st.divider()

# === SECTION 4: VISUALISASI DETAIL ===
with st.expander("📈 Lihat Visualisasi Detail Lainnya"):
    st.subheader("Histogram Sebaran Pinjaman")
    
    histogram_file = get_latest_file(vis_dir, "cluster_histogram_*.png")
    
    if histogram_file and os.path.exists(histogram_file):
        try:
            img = Image.open(histogram_file)
            st.image(img, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Histogram belum tersedia")

st.divider()

# === SECTION 5: ANALISIS TEMPORAL (PAKAI ANGKA PENUH) ===
st.header("📅 Analisis Temporal (Jatuh Tempo)")

temporal_charts = [
    ("Total Pinjaman per Tanggal", "temporal_total_pinjaman_*.png"),
    ("Jumlah Nasabah per Tanggal", "temporal_jumlah_nasabah_*.png"),
    ("Segmen Pinjaman per Tanggal", "temporal_segment_stacked_*.png"),
]

# Cek apakah ada visualisasi temporal
has_temporal = any(get_latest_file(vis_dir, pattern) for _, pattern in temporal_charts)

if has_temporal:
    st.markdown("*Visualisasi tren pinjaman berdasarkan tanggal jatuh tempo dengan angka lengkap*")
    
    # Baris 1: Total Pinjaman & Jumlah Nasabah
    cols_temp1 = st.columns(2)
    for idx in range(2):
        if idx < len(temporal_charts):
            title, pattern = temporal_charts[idx]
            chart_file = get_latest_file(vis_dir, pattern)
            
            with cols_temp1[idx]:
                if chart_file and os.path.exists(chart_file):
                    st.subheader(title)
                    try:
                        img = Image.open(chart_file)
                        st.image(img, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    # Baris 2: Segmen per Tanggal (full width)
    if len(temporal_charts) > 2:
        title, pattern = temporal_charts[2]
        chart_file = get_latest_file(vis_dir, pattern)
        
        if chart_file and os.path.exists(chart_file):
            st.subheader(title)
            try:
                img = Image.open(chart_file)
                st.image(img, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("ℹ️ Visualisasi temporal tidak tersedia (data tidak memiliki kolom TGL_JATUH_TEMPO)")

st.divider()

# === SECTION 6: RINGKASAN SEGMEN ===
st.header("📑 Ringkasan Segmen Nasabah")

latest_summary_csv = get_latest_file(summary_dir, "cluster_summary_*.csv")
latest_summary_txt = get_latest_file(summary_dir, "cluster_summary_*.txt")

if latest_summary_csv:
    summary_df = pd.read_csv(latest_summary_csv)
    st.dataframe(summary_df, use_container_width=True)
    
    # Tampilkan summary text jika ada
    if latest_summary_txt:
        with st.expander("📄 Lihat Ringkasan Detail"):
            with open(latest_summary_txt, "r", encoding="utf-8") as f:
                st.text(f.read())
else:
    st.info("ℹ️ Belum ada summary segmen - jalankan pipeline untuk menghasilkan ringkasan.")

# Footer
st.divider()
st.caption("💡 Tip: Gunakan ekspander untuk melihat detail data dan visualisasi tambahan")