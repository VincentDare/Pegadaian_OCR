import streamlit as st
import os

DATASET_DIR = "dataset"
folder_mapping = {
    "jatuh tempo": "Dataset Daftar Kredit Jatuh Tempo",
    "kredit bermasalah": "Dataset Daftar Kredit Bermasalah"
}

st.title("📂 Upload Dokumen")
st.markdown("### Langkah 1: Upload file PDF Anda")

# Info box
with st.expander("ℹ️ Panduan Upload"):
    st.markdown("""
    **Tipe Dokumen:**
    - **Jatuh Tempo**: Daftar kredit yang akan jatuh tempo
    - **Kredit Bermasalah**: Daftar kredit yang bermasalah
    
    **Format File:**
    - Format: PDF
    - Ukuran maksimal: 200MB per file
    - Dapat upload multiple files sekaligus
    """)

uploaded_files = st.file_uploader(
    "Pilih file PDF", 
    type=["pdf"], 
    accept_multiple_files=True,
    help="Dapat memilih lebih dari satu file PDF"
)

doc_type = st.selectbox(
    "Tipe Dokumen", 
    ["jatuh tempo", "kredit bermasalah"],
    help="Pilih sesuai dengan jenis dokumen yang diupload"
)

if uploaded_files:
    st.info(f"📄 {len(uploaded_files)} file siap diupload ke tipe '{doc_type}'")
    
    # Show file list
    with st.expander("Lihat daftar file"):
        for i, f in enumerate(uploaded_files, 1):
            st.write(f"{i}. {f.name} ({f.size / 1024:.2f} KB)")
    
    if st.button("💾 Simpan PDF ke Folder", type="primary", use_container_width=True):
        with st.spinner("Menyimpan file..."):
            target_dir = os.path.join(DATASET_DIR, folder_mapping[doc_type])
            os.makedirs(target_dir, exist_ok=True)
            
            for uploaded_file in uploaded_files:
                pdf_path = os.path.join(target_dir, uploaded_file.name)
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.read())
            
            st.success(f"✅ {len(uploaded_files)} file berhasil disimpan ke {folder_mapping[doc_type]}")
            st.balloons()
            
            # Auto redirect
            st.info("🔄 Mengarahkan ke halaman Template Message...")
            st.session_state.uploaded_files_count = len(uploaded_files)
            st.switch_page("pages/2_template_message.py")
else:
    st.warning("⚠️ Silakan upload minimal 1 file PDF untuk melanjutkan")