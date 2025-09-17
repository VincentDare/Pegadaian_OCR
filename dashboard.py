# streamlit_app.py
import streamlit as st
import pandas as pd
import glob, os, time,  base64
import json
import pipeline  

# ===== Konfigurasi dasar =====
st.set_page_config(page_title="Pegadaian OCR & Clustering", layout="wide")
st.title("📂 Pegadaian OCR & Clustering Dashboard")

DATASET_DIR = "dataset"
OUTPUT_DIR = "output"
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
# Pastikan subfolder hasil pipeline ada
os.makedirs(os.path.join(OUTPUT_DIR, "parsed_output"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "messages"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "missing"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "clustering"), exist_ok=True)

# Mapping subfolder untuk dataset
folder_mapping = {
    "jatuh tempo": "Dataset Daftar Kredit Jatuh Tempo",
    "kredit bermasalah": "Dataset Daftar Kredit Bermasalah"
}

# ===== 1. Upload Dokumen =====
st.subheader("Upload Dokumen")
uploaded_files = st.file_uploader(
    "Pilih file PDF (bisa lebih dari satu)",
    type=["pdf"],
    accept_multiple_files=True
)
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

def hapus_file(pdf_path):
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        st.session_state['file_deleted'] = True

st.subheader("Daftar Dokumen")

pdf_files = []
for subfolder in folder_mapping.values():
    folder_path = os.path.join(DATASET_DIR, subfolder)
    if os.path.exists(folder_path):
        for f in os.listdir(folder_path):
            if f.endswith(".pdf"):
                pdf_files.append((f, folder_path))

if not pdf_files:
    st.info("Belum ada dokumen yang diproses.")
else:
    for pdf_file, folder_path in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        with st.expander(f"📄 {pdf_file}"):
            if st.button(f"❌ Hapus {pdf_file}", key=f"hapus_{pdf_file}"):
                try:
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    st.success(f"{pdf_file} berhasil dihapus.")
                    st.rerun()  
                except Exception as e:
                    st.error(f"Gagal hapus file: {e}")

# ===== 2. Custom Text untuk Messages =====
st.subheader("Custom Text untuk Messages")
template_doc_type = doc_type  

template_path = os.path.join("config", "templates.json")
if os.path.exists(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        templates = json.load(f)
else:
    templates = {"jatuh_tempo": "", "kredit_bermasalah": ""}

# ----- Pastikan text area selalu kosong saat Streamlit start -----
if "custom_text" not in st.session_state:
    st.session_state.custom_text = ""  

# Placeholder tombol
placeholders = {
    "jatuh tempo": ["{NO_SBG}", "{NASABAH}", "{TGL_JATUH_TEMPO}", "{UANG_PINJAMAN}"],
    "kredit bermasalah": ["{NO_KREDIT}", "{NASABAH}", "{UANG_PINJAMAN}"]
}

ph_list = placeholders[template_doc_type]
max_cols = 4
for i in range(0, len(ph_list), max_cols):
    cols = st.columns(min(max_cols, len(ph_list) - i))
    for j, ph in enumerate(ph_list[i:i+max_cols]):
        if cols[j].button(ph, key=f"btn_{template_doc_type}_{ph}"):
            st.session_state.custom_text += ph + " "

# Text area
st.session_state.custom_text = st.text_area(
    "Template Pesan",
    st.session_state.custom_text,
    height=200,
    key="custom_text_area"
)

# Inisialisasi session_state
if "save_notification" not in st.session_state:
    st.session_state.save_notification = ""
if "notif_time" not in st.session_state:
    st.session_state.notif_time = 0.0

# Placeholder untuk notifikasi
notification_placeholder = st.empty()

def save_template():
    # Simpan ke JSON
    templates[template_doc_type] = st.session_state.custom_text
    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)
    
    # Kosongkan text area
    st.session_state.custom_text = ""
    
    # Tampilkan notifikasi
    st.session_state.save_notification = f"Template untuk {template_doc_type} berhasil diperbarui!"
    st.session_state.notif_time = time.time()

st.button(f"Simpan Template ({template_doc_type})", on_click=save_template)

# Tampilkan notifikasi jika masih dalam 10 detik
if st.session_state.save_notification:
    elapsed = time.time() - st.session_state.notif_time
    if elapsed < 10:
        notification_placeholder.success(st.session_state.save_notification)
    else:
        notification_placeholder.empty()
        st.session_state.save_notification = ""

# ===== 3. Jalankan Semua Pipeline =====
st.subheader("Jalankan Model OCR")
if st.button("Jalankan OCR"):
    with st.spinner("Sedang menjalankan pipeline untuk semua PDF..."):
        pipeline.run_pipeline_all()
    st.success("✅ Semua pipeline selesai dijalankan!")

# ===== 4. Hapus Semua Data =====
if "show_delete_popup" not in st.session_state:
    st.session_state.show_delete_popup = False

# === Timer Upload ===
if "last_upload_time" not in st.session_state:
    st.session_state.last_upload_time = None

# Kalau ada file baru diupload → set timestamp
if uploaded_files:
    st.session_state.last_upload_time = time.time()

# === Fungsi hapus data ===
def hapus_semua_data():
    deleted_count = 0
    skipped = []
    for folder in [DATASET_DIR, "images", OUTPUT_DIR]:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.endswith(".pkl"):  # model tetap aman
                        skipped.append(f)
                        continue
                    try:
                        os.remove(os.path.join(root, f))
                        deleted_count += 1
                    except Exception as e:
                        st.warning(f"Gagal hapus {f}: {e}")
    return deleted_count, skipped

# === Auto delete setelah 30 menit ===
if st.session_state.last_upload_time:
    elapsed = time.time() - st.session_state.last_upload_time
    if elapsed > 1800:  # 30 menit
        deleted_count, skipped = hapus_semua_data()
        st.success(f"✅ {deleted_count} file otomatis dihapus setelah 30 menit. "
                   f"Model (.pkl) tetap aman ({len(skipped)} file).")
        st.session_state.last_upload_time = None
        st.rerun()

# === Manual delete pakai tombol ===
st.subheader("Hapus Semua Data")

if "show_delete_popup" not in st.session_state:
    st.session_state.show_delete_popup = False

if not st.session_state.show_delete_popup:
    if st.button("⚠️ Hapus Semua Dokumen"):
        st.session_state.show_delete_popup = True
        st.rerun()
else:
    st.error("Apakah kamu yakin ingin menghapus semua data? Aksi ini tidak bisa dibatalkan!")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Ya, hapus semua data"):
            deleted_count, skipped = hapus_semua_data()
            st.success(f"✅ {deleted_count} file dihapus. Model (.pkl) tetap aman ({len(skipped)} file).")
            st.session_state.show_delete_popup = False
            st.session_state.last_upload_time = None
            st.rerun()

    with col2:
        if st.button("❌ Batal"):
            st.session_state.show_delete_popup = False
            st.rerun()


# ===== Menu Download Hasil Pipeline (Tombol Rapi) =====
st.subheader("Download Hasil OCR")

parsed_dir = os.path.join(OUTPUT_DIR, "parsed_output")
messages_dir = os.path.join(OUTPUT_DIR, "messages")
missing_dir = os.path.join(OUTPUT_DIR, "missing")

# Ambil file terakhir tiap output (atau bisa semua file)
latest_parsed = max([os.path.join(parsed_dir, f) for f in os.listdir(parsed_dir) if f.endswith("_extracted.csv")], default=None)
latest_message = max([os.path.join(messages_dir, f) for f in os.listdir(messages_dir) if f.endswith(".xlsx")], default=None)
latest_missing = max([os.path.join(missing_dir, f) for f in os.listdir(missing_dir) if f.endswith(".csv")], default=None)

cols = st.columns(3)

with cols[0]:
    if latest_parsed and os.path.exists(latest_parsed):
        with open(latest_parsed, "rb") as f:
            st.download_button("⬇️ Download Parsed", f, file_name=os.path.basename(latest_parsed))
    else:
        st.write("⚠️ Parsed belum tersedia")

with cols[1]:
    if latest_message and os.path.exists(latest_message):
        with open(latest_message, "rb") as f:
            st.download_button("⬇️ Download Message", f, file_name=os.path.basename(latest_message))
    else:
        st.write("⚠️ Message belum tersedia")

with cols[2]:
    if latest_missing and os.path.exists(latest_missing):
        with open(latest_missing, "rb") as f:
            st.download_button("⬇️ Download Missing", f, file_name=os.path.basename(latest_missing))
    else:
        st.write("⚠️ Missing belum tersedia")

st.subheader("Preview Hasil OCR")
# ===== 6. Preview Parsed / Missing =====
st.subheader("Parsed Document / Missing Names")
parsed_dir = os.path.join(OUTPUT_DIR, "parsed_output")
missing_dir = os.path.join(OUTPUT_DIR, "missing")
option = st.selectbox("Pilih Data", ["Parsed Document", "Missing Names"])
if option == "Parsed Document":
    if os.path.exists(parsed_dir):
        files = [f for f in os.listdir(parsed_dir) if f.endswith("_extracted.csv")]
        if files:
            selected_file = st.selectbox("Pilih file parsed", files)
            df = pd.read_csv(os.path.join(parsed_dir, selected_file))
            st.dataframe(df.head(5))
        else: st.warning("Belum ada hasil parsed.")
    else: st.warning("Folder parsed_output belum ada.")
elif option == "Missing Names":
    if os.path.exists(missing_dir):
        files = [f for f in os.listdir(missing_dir) if f.endswith(".csv")]
        if files:
            selected_file = st.selectbox("Pilih file missing", files)
            df = pd.read_csv(os.path.join(missing_dir, selected_file))
            st.dataframe(df.head(5))
        else: st.info("Tidak ada missing names.")
    else: st.warning("Folder missing belum ada.")

# ===== 7. Preview Messages =====
st.subheader("Message")
msg_dir = os.path.join(OUTPUT_DIR, "messages")
if os.path.exists(msg_dir):
    files = [f for f in os.listdir(msg_dir) if f.endswith(".csv") or f.endswith(".xlsx")]
    if files:
        selected_msg = st.selectbox("Pilih file message", files)
        file_path = os.path.join(msg_dir, selected_msg)
        df_msg = pd.read_csv(file_path) if selected_msg.endswith(".csv") else pd.read_excel(file_path)
        st.dataframe(df_msg.head(5))
    else: st.info("Belum ada messages.")
else: st.warning("Folder messages belum ada.")

# ===== 8. Clustering & Visualisasi =====
st.subheader("Clustering Visualize & Summary")
clustered_file = os.path.join(OUTPUT_DIR, "clustering", "model", "clustered_data.csv")
summary_dir = os.path.join(OUTPUT_DIR, "clustering", "summary")
summary_files = glob.glob(os.path.join(summary_dir, "cluster_summary_*.csv"))
latest_summary = max(summary_files, key=os.path.getctime) if summary_files else None

st.markdown("""
<style>
.chart-img { 
    width: 120%;   /* Lebarkan bar chart */
    height: 300px; 
    object-fit: contain; 
}
.chart-img-pie { 
    width: 90%;    /* Pie chart lebih besar */
    height: 380px; 
    object-fit: contain; 
    display: block; 
    margin-left: auto; 
    margin-right: auto; 
}
</style>
""", unsafe_allow_html=True)

def render_chart(title, file_path, pie=False):
    st.markdown(f"**{title}**")
    if file_path and os.path.exists(file_path):
        img_base64 = base64.b64encode(open(file_path, "rb").read()).decode()
        css_class = "chart-img-pie" if pie else "chart-img"
        st.markdown(f'<img src="data:image/png;base64,{img_base64}" class="{css_class}"/>',
                    unsafe_allow_html=True)
    else:
        st.info("⚠️ Chart belum tersedia.")

if os.path.exists(clustered_file):
    clustered_df = pd.read_csv(clustered_file)

    if "CLUSTER_LABEL" not in clustered_df.columns:
        cluster_order = clustered_df.groupby("CLUSTER")["UANG_PINJAMAN"].mean().sort_values().index.tolist()
        cluster_labels = {
            cluster_order[0]: "Pinjaman Kecil",
            cluster_order[1]: "Pinjaman Menengah",
            cluster_order[2]: "Pinjaman Besar"
        }
        clustered_df["CLUSTER_LABEL"] = clustered_df["CLUSTER"].map(cluster_labels)

    if latest_summary:
        st.dataframe(pd.read_csv(latest_summary), use_container_width=True)
    else:
        st.info("⚠️ Belum ada summary yang tersedia.")

    vis_dir = os.path.join(OUTPUT_DIR, "clustering", "visualization")

    def get_latest_chart(prefix):
        files = glob.glob(os.path.join(vis_dir, f"{prefix}_*.png"))
        return max(files, key=os.path.getctime) if files else None

    avg_file = get_latest_chart("cluster_bar")
    count_file = get_latest_chart("cluster_count_bar")
    pie_file = get_latest_chart("cluster_pie")

    # Bar chart di atas (2 kolom)
    col1, col2 = st.columns(2)
    with col1:
        render_chart("Rata-rata Pinjaman per Segmen", avg_file)
    with col2:
        render_chart("Jumlah Nasabah per Segmen", count_file)

    st.markdown("---")

    # Pie chart di bawah, lebih besar
    render_chart("Distribusi Nasabah (Pie Chart)", pie_file, pie=True)

else:
    st.info("⚠️ Belum ada hasil clustering yang tersedia.")

