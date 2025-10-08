import streamlit as st
import os
import pandas as pd
from io import BytesIO

OUTPUT_DIR = "output"
parsed_dir = os.path.join(OUTPUT_DIR, "parsed_output") 
messages_dir = os.path.join(OUTPUT_DIR, "messages")
missing_dir = os.path.join(OUTPUT_DIR, "missing")
raw_ocr_dir = os.path.join(OUTPUT_DIR, "raw_ocr")

st.title("📑 Output & Download")
st.markdown("### Hasil Pemrosesan Dokumen")

# Pipeline completion status
if "pipeline_completed" in st.session_state:
    st.success("✅ Pipeline berhasil dijalankan!")

# Info directories
with st.expander("📂 Informasi Direktori Output"):
    st.code(f"""
    Parsed Data: {parsed_dir}
    Messages: {messages_dir}
    Raw OCR: {raw_ocr_dir}
    Missing: {missing_dir}
    """)

# Tabs untuk berbagai output
tab1, tab2, tab3, = st.tabs(["📄 Parsed Data", "📧 Messages",  "🔍 Raw OCR"])

# === TAB 1: PARSED DATA ===
with tab1:
    st.markdown("### Data yang Sudah Diproses")
    
    if os.path.exists(parsed_dir):
        # Cari semua file CSV di folder parsed
        all_files = [f for f in os.listdir(parsed_dir) if f.endswith(".csv")]
        
        if all_files:
            st.info(f"📁 Ditemukan {len(all_files)} file parsed")
            
            selected_file = st.selectbox("Pilih file parsed", all_files, key="parsed_select")
            file_path = os.path.join(parsed_dir, selected_file)
            
            try:
                df = pd.read_csv(file_path)
                
                # ✅ FIX: Convert ALL possible numeric column variations
                numeric_cols = [
                    'UANG_PINJAMAN', 'Uang_Pinjaman', 'uang_pinjaman',
                    'TAKSIRAN', 'Taksiran', 'taksiran',
                    'SM', 'Sm', 'sm'
                ]
                
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                # Data preview
                st.markdown("#### 📋 Preview Data")
                st.dataframe(df, use_container_width=True, height=400)
                
                # Column info
                with st.expander("ℹ️ Informasi Kolom"):
                    col_info = pd.DataFrame({
                        'Kolom': df.columns,
                        'Tipe': df.dtypes.values,
                        'Non-Null': [df[col].notna().sum() for col in df.columns],
                        'Null': [df[col].isna().sum() for col in df.columns]
                    })
                    st.dataframe(col_info, use_container_width=True)
                
                st.divider()
                
                # Download section
                st.markdown("### 💾 Download Data")
                col1, = st.columns(1)
            
                with col1:
                    # CSV download
                    csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"{selected_file}",
                        mime="text/csv",
                        use_container_width=True
                    )
                
            except Exception as e:
                st.error(f"❌ Error membaca file: {str(e)}")
                with st.expander("Detail Error"):
                    st.exception(e)
        else:
            st.warning("⚠️ Belum ada hasil parsed. Jalankan pipeline terlebih dahulu.")
            if st.button("🔄 Jalankan Pipeline"):
                st.switch_page("pages/3_jalankan_ocr.py")
    else:
        st.info("ℹ️ Folder parsed belum tersedia. Jalankan pipeline terlebih dahulu.")
        if st.button("🔄 Jalankan Pipeline"):
            st.switch_page("pages/3_jalankan_ocr.py")

# === TAB 2: MESSAGES ===
with tab2:
    st.markdown("### 📧 Pesan WhatsApp yang Dihasilkan")
    
    if os.path.exists(messages_dir):
        files = [f for f in os.listdir(messages_dir) if f.endswith((".csv", ".xlsx"))]
        
        if files:
            st.info(f"📁 Ditemukan {len(files)} file message")
            
            selected_file = st.selectbox("Pilih file message", files, key="msg_select")
            file_path = os.path.join(messages_dir, selected_file)
            
            try:
                df = pd.read_csv(file_path) if selected_file.endswith(".csv") else pd.read_excel(file_path)
                
                st.metric("Total Pesan", f"{len(df):,}")
                
                # Preview messages
                if 'message' in df.columns or 'Message' in df.columns:
                    msg_col = 'message' if 'message' in df.columns else 'Message'
                    
                    st.markdown("####  Preview Pesan")
                    with st.expander("Lihat 5 pesan pertama", expanded=True):
                        for i, msg in enumerate(df[msg_col].head(), 1):
                            st.text_area(f"Pesan {i}", str(msg), height=120, disabled=True, key=f"msg_preview_{i}")
                
                st.divider()
                
                # Data table
                st.markdown("#### 📋 Data Lengkap")
                st.dataframe(df, use_container_width=True, height=400)
                
                st.divider()
                
                # Download
                st.markdown("### 💾 Download Messages")
                col1, = st.columns(1)
                
                with col1:
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Messages')
                    excel_data = buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_data,
                        file_name=selected_file if selected_file.endswith('.xlsx') else selected_file.replace('.csv', '.xlsx'),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
            except Exception as e:
                st.error(f"❌ Error membaca file: {str(e)}")
                with st.expander("Detail Error"):
                    st.exception(e)
        else:
            st.info("ℹ️ Belum ada messages yang di-generate.")
    else:
        st.info("ℹ️ Folder messages belum tersedia.")

# === TAB 4: RAW OCR ===
with tab3:
    st.markdown("### 🔍 Raw OCR Output")
    st.caption("Hasil mentah dari OCR sebelum diproses dan dibersihkan")
    
    if os.path.exists(raw_ocr_dir):
        files = [f for f in os.listdir(raw_ocr_dir) if f.endswith(".csv") and "REVIEW" not in f.upper()]
        
        if files:
            st.info(f"📁 Ditemukan {len(files)} file raw OCR")
            
            selected_file = st.selectbox("Pilih file raw", files, key="raw_select")
            file_path = os.path.join(raw_ocr_dir, selected_file)
            
            try:
                df = pd.read_csv(file_path)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Record", f"{len(df):,}")
                with col2:
                    st.metric("Jumlah Kolom", len(df.columns))
                
                st.divider()
                
                # Download (PINDAH KE ATAS)
                csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Download Raw OCR (CSV)",
                    data=csv,
                    file_name=selected_file,
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.divider()
                
                # Preview dengan expander
                with st.expander("📋 Preview Data", expanded=False):
                    st.dataframe(df, use_container_width=True, height=400)
                
                with st.expander("ℹ️ Informasi Raw OCR"):
                    st.markdown("""
                    **Raw OCR** adalah hasil langsung dari proses OCR sebelum:
                    - Pembersihan data
                    - Normalisasi format
                    - Validasi
                    - Parsing
                    
                    Data ini berguna untuk:
                    - Debugging masalah OCR
                    - Analisis akurasi OCR
                    - Training model OCR
                    """)
                
            except Exception as e:
                st.error(f"❌ Error membaca file: {str(e)}")
                with st.expander("Detail Error"):
                    st.exception(e)
        else:
            st.info("ℹ️ Belum ada raw OCR output.")
    else:
        st.info("ℹ️ Folder raw OCR belum tersedia.")

st.divider()

# Navigation
st.markdown("### Navigasi")
col1, col2 = st.columns(2)

with col1:
    if st.button("⏪ Kembali ke Pipeline", use_container_width=True):
        st.switch_page("pages/3_jalankan_ocr.py")

with col2:
    if st.button("⏩ Lanjut ke Clustering", use_container_width=True):
        st.switch_page("pages/5_clustering.py")

# Footer info
st.divider()
st.caption("💡 Tip: Gunakan tab di atas untuk melihat berbagai jenis output dari pipeline")