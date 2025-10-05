import streamlit as st
import pipeline

st.title("⚙️ Jalankan OCR")

if st.button("▶️ Mulai Proses OCR"):
    progress_bar = st.progress(0, text="Menjalankan pipeline...")

    pipeline.run_pipeline_all(
        update_progress=lambda p, msg: progress_bar.progress(p, text=msg)
    )

    st.success("✅ Semua pipeline selesai dijalankan!")
