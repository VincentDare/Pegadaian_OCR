import streamlit as st
import pipeline
import os
import time

st.title("🔄 Jalankan OCR & Pipeline")
st.markdown("### Langkah 3: Proses dokumen dengan OCR")

# Check if files uploaded
DATASET_DIR = "dataset"
jt_dir = os.path.join(DATASET_DIR, "Dataset Daftar Kredit Jatuh Tempo")
kb_dir = os.path.join(DATASET_DIR, "Dataset Daftar Kredit Bermasalah")

# Safe file listing dengan error handling
def get_pdf_files(directory):
    try:
        if os.path.exists(directory):
            return [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
        return []
    except Exception as e:
        st.error(f"Error membaca folder {directory}: {e}")
        return []

jt_files = get_pdf_files(jt_dir)
kb_files = get_pdf_files(kb_dir)

# Status overview
st.markdown("### 📊 Status Dokumen")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📄 Jatuh Tempo", len(jt_files))
with col2:
    st.metric("📄 Kredit Bermasalah", len(kb_files))
with col3:
    total_files = len(jt_files) + len(kb_files)
    st.metric("📄 Total", total_files)

# Template status
template_path = os.path.join("config", "templates.json")
template_exists = os.path.exists(template_path)

col1, col2 = st.columns(2)
with col1:
    if template_exists:
        st.success("✅ Template pesan tersedia")
    else:
        st.warning("⚠️ Template belum dibuat")
        
with col2:
    # Check if images folder exists (sudah preprocessing)
    images_exist = os.path.exists("images") and (
        os.path.exists(os.path.join("images", "jatuh_tempo")) or 
        os.path.exists(os.path.join("images", "kredit_bermasalah"))
    )
    if images_exist:
        st.info("ℹ️ Preprocessing sudah pernah dijalankan")
    else:
        st.info("ℹ️ Preprocessing belum pernah dijalankan")

# Pipeline info
with st.expander("ℹ️ Tahapan Pipeline"):
    st.markdown("""
    **Proses yang akan dijalankan:**
    
    1. **📸 Preprocessing PDF** - Konversi PDF ke gambar berkualitas tinggi
    2. **🔍 OCR Extraction** - Ekstrak teks dari gambar menggunakan EasyOCR
    3. **🧹 Postprocessing** - Bersihkan dan normalisasi hasil OCR
    4. **✨ Cleaning** - Validasi dan perbaiki data
    5. **📝 Parsing** - Generate pesan WhatsApp untuk nasabah
    6. **📊 Dataset Merge** - Gabungkan semua data menjadi satu
    7. **🔬 Preprocessing Clustering** - Persiapan data untuk machine learning
    8. **📈 EDA** - Analisis data eksploratori
    9. **🤖 Clustering** - Segmentasi nasabah dengan K-Means
    10. **✅ Evaluation** - Evaluasi kualitas clustering
    11. **📊 Visualization** - Buat visualisasi hasil analisis
    
    **Estimasi waktu:** 
    - 1-5 file: ~3-5 menit
    - 5-10 file: ~5-10 menit
    - 10+ file: ~10-15 menit
    
    **💡 Tips:** Proses bisa memakan waktu lama tergantung jumlah halaman PDF dan spesifikasi komputer.
    """)

st.divider()

# Warning jika tidak ada file
if total_files == 0:
    st.error("❌ Tidak ada file PDF yang diupload. Silakan upload file terlebih dahulu.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📂 Kembali ke Upload", use_container_width=True):
            st.switch_page("pages/1_upload_dokumen.py")
    with col2:
        if st.button("❓ Bantuan", use_container_width=True):
            st.info("""
            **Cara Upload Dokumen:**
            1. Klik 'Kembali ke Upload'
            2. Pilih tipe dokumen (Jatuh Tempo / Kredit Bermasalah)
            3. Upload file PDF Anda
            4. Klik 'Simpan' lalu kembali ke halaman ini
            """)
    
    st.stop()

# Main process section
st.markdown("###Mulai Proses")

# Show files to process
with st.expander("📂 Lihat file yang akan diproses", expanded=False):
    if jt_files:
        st.markdown("**📄 Jatuh Tempo:**")
        for i, f in enumerate(jt_files, 1):
            file_size = os.path.getsize(os.path.join(jt_dir, f)) / 1024  # KB
            st.write(f"{i}. {f} ({file_size:.1f} KB)")
    
    if kb_files:
        st.markdown("**📄 Kredit Bermasalah:**")
        for i, f in enumerate(kb_files, 1):
            file_size = os.path.getsize(os.path.join(kb_dir, f)) / 1024  # KB
            st.write(f"{i}. {f} ({file_size:.1f} KB)")

# Warning sebelum proses
st.warning("""
⚠️ **Perhatian:**
- Proses ini akan memakan waktu beberapa menit
- Jangan tutup browser atau refresh halaman
- Pastikan koneksi internet stabil (untuk download model OCR pertama kali)
""")

# Process button
if st.button("▶️ MULAI PROSES OCR", type="primary", use_container_width=True):
    
    # Initialize session state untuk tracking
    if 'pipeline_running' not in st.session_state:
        st.session_state.pipeline_running = False
    
    if st.session_state.pipeline_running:
        st.warning("⚠️ Pipeline sedang berjalan. Mohon tunggu hingga selesai.")
        st.stop()
    
    st.session_state.pipeline_running = True
    
    # UI Elements
    progress_bar = st.progress(0, text="Memulai pipeline...")
    status_text = st.empty()
    log_expander = st.expander("📋 Log Detail", expanded=False)
    logs = []
    
    def update_progress(percent, message):
        progress_bar.progress(percent / 100, text=f"{message} ({percent}%)")
        status_text.info(f" {message}")
        logs.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        with log_expander:
            st.text("\n".join(logs[-20:]))  # Show last 20 logs
    
    start_time = time.time()
    
    try:
        update_progress(0, "Memulai pipeline...")
        
        # Run pipeline
        pipeline.run_pipeline_all(update_progress=update_progress)
        
        # Success
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        progress_bar.progress(100, text="✅ Pipeline selesai!")
        status_text.success(f"Semua proses berhasil diselesaikan dalam {minutes}m {seconds}s!")
        
        st.balloons()
        
        # Summary
        st.markdown("### ✅ Ringkasan Hasil")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Waktu Proses", f"{minutes}m {seconds}s")
        with col2:
            st.metric("File Diproses", total_files)
        with col3:
            st.metric("Status", "✅ Sukses", delta="100%")
        
        # Show output info
        st.info("""
        **📂 Output yang Dihasilkan:**
        - Raw OCR results (CSV)
        - Parsed data & WhatsApp messages
        - Clustering results
        - Visualizations (charts & graphs)
        """)
        
        # Navigation
        time.sleep(2)
        st.info("🔄 Mengarahkan ke halaman Output dalam 3 detik...")
        time.sleep(1)
        
        st.session_state.pipeline_completed = True
        st.session_state.pipeline_running = False
        st.switch_page("pages/4_output_parsed.py")
        
    except FileNotFoundError as e:
        st.session_state.pipeline_running = False
        st.error(f"❌ File tidak ditemukan: {str(e)}")
        st.warning("Pastikan semua file PDF sudah diupload dengan benar.")
        
        if st.button("🔄 Coba Lagi"):
            st.rerun()
            
    except MemoryError:
        st.session_state.pipeline_running = False
        st.error("❌ Memory tidak cukup! Coba proses file lebih sedikit atau restart aplikasi.")
        st.info("💡 Saran: Proses file secara bertahap (misal 5 file per proses)")
        
    except Exception as e:
        st.session_state.pipeline_running = False
        st.error(f"❌ Terjadi kesalahan: {str(e)}")
        
        with st.expander("🔍 Detail Error"):
            st.exception(e)
        
        st.markdown("""
        **Troubleshooting:**
        1. Pastikan semua dependencies terinstall
        2. Cek apakah file PDF tidak corrupt
        3. Restart aplikasi dan coba lagi
        4. Hubungi developer jika error berlanjut
        """)
        
        if st.button("🔄 Coba Lagi"):
            st.rerun()

st.divider()

# Additional actions
col1, col2 = st.columns(2)

with col1:
    if st.button("⏪ Kembali ke Template", use_container_width=True):
        st.switch_page("pages/2_template_message.py")

with col2:
    if st.button("⏩ Skip ke Output", use_container_width=True):
        # Check if output exists
        output_exists = os.path.exists("output") and os.path.exists(os.path.join("output", "parsed"))
        if output_exists:
            st.switch_page("pages/4_output_parsed.py")
        else:
            st.warning("⚠️ Belum ada output. Jalankan pipeline terlebih dahulu.")