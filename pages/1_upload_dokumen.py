import streamlit as st
import os

DATASET_DIR = "dataset"
folder_mapping = {
    "jatuh tempo": "Dataset Daftar Kredit Jatuh Tempo",
    "kredit bermasalah": "Dataset Daftar Kredit Bermasalah"
}

st.title("📂 Upload Dokumen")

uploaded_files = st.file_uploader("Pilih file PDF", type=["pdf"], accept_multiple_files=True)
doc_type = st.selectbox("Tipe Dokumen", ["jatuh tempo", "kredit bermasalah"])

if uploaded_files:
    st.info(f"{len(uploaded_files)} file siap diupload ke tipe '{doc_type}'.")
    if st.button("📂 Simpan PDF ke Folder"):
        target_dir = os.path.join(DATASET_DIR, folder_mapping[doc_type])
        os.makedirs(target_dir, exist_ok=True)
        for uploaded_file in uploaded_files:
            pdf_path = os.path.join(target_dir, uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())
        st.success(f"{len(uploaded_files)} file berhasil disimpan ke {folder_mapping[doc_type]}.")
