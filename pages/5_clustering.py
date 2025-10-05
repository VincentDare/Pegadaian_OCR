import streamlit as st
import os, glob, pandas as pd, base64

OUTPUT_DIR = "output"

st.title("📊 Clustering & Visualisasi")

clustered_file = os.path.join(OUTPUT_DIR, "clustering", "model", "clustered_data.csv")
summary_dir = os.path.join(OUTPUT_DIR, "clustering", "summary")
summary_files = glob.glob(os.path.join(summary_dir, "cluster_summary_*.csv"))
latest_summary = max(summary_files, key=os.path.getctime) if summary_files else None

if os.path.exists(clustered_file):
    clustered_df = pd.read_csv(clustered_file)
    if latest_summary:
        st.dataframe(pd.read_csv(latest_summary), use_container_width=True)
    else:
        st.info("⚠️ Belum ada summary.")

    vis_dir = os.path.join(OUTPUT_DIR, "clustering", "visualization")

    def get_latest_chart(prefix):
        files = glob.glob(os.path.join(vis_dir, f"{prefix}_*.png"))
        return max(files, key=os.path.getctime) if files else None

    avg_file = get_latest_chart("cluster_bar")
    count_file = get_latest_chart("cluster_count_bar")
    pie_file = get_latest_chart("cluster_pie")

    for title, file_path in [("Rata-rata Pinjaman", avg_file),
                             ("Jumlah Nasabah", count_file),
                             ("Distribusi Nasabah", pie_file)]:
        if file_path and os.path.exists(file_path):
            img_base64 = base64.b64encode(open(file_path, "rb").read()).decode()
            st.markdown(f'<img src="data:image/png;base64,{img_base64}" style="width:100%"/>',
                        unsafe_allow_html=True)
        else:
            st.warning(f"{title} chart belum tersedia")
else:
    st.warning("⚠️ Belum ada hasil clustering.")
