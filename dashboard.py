import streamlit as st

st.set_page_config(
    page_title="Pegadaian OCR & Clustering", 
    layout="wide",
    page_icon="🏦"
)

# Header
st.title("Pegadaian OCR & Clustering App")
st.markdown("### Sistem Analisis Dokumen Kredit & Segmentasi Nasabah")
st.divider()

# Welcome Section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## Selamat Datang!
    
    Aplikasi ini membantu Anda untuk:
    - 📄 **Ekstraksi data** dari dokumen PDF kredit
    - 🤖 **OCR otomatis** untuk digitalisasi dokumen
    - 📊 **Clustering nasabah** berdasarkan pola pinjaman
    - 📈 **Visualisasi** segmentasi dan analisis temporal
    - 💬 **Template pesan** untuk komunikasi nasabah
    """)
    
    # Tombol Mulai Besar
    st.markdown("### Mulai Sekarang")
    if st.button("▶️ MULAI UPLOAD DOKUMEN", type="primary", use_container_width=True):
        st.switch_page("pages/1_upload_dokumen.py")

# Menu Navigasi Interaktif
st.markdown("## Menu Navigasi")

# Definisi menu
menu_items = [
    {
        "icon": "📤",
        "title": "Upload Dokumen",
        "desc": "Upload file PDF kredit jatuh tempo & bermasalah",
        "page": "pages/1_upload_dokumen.py",
        "color": "#FF6B6B"
    },
    {
        "icon": "💬",
        "title": "Template Message",
        "desc": "Buat template pesan untuk nasabah",
        "page": "pages/2_template_message.py",
        "color": "#4ECDC4"
    },
    {
        "icon": "⚙️",
        "title": "Pipeline (OCR & Parsing)",
        "desc": "Jalankan OCR dan ekstraksi data otomatis",
        "page": "pages/3_pipeline.py",
        "color": "#45B7D1"
    },
    {
        "icon": "📋",
        "title": "Output Parsed",
        "desc": "Lihat hasil ekstraksi data dari PDF",
        "page": "pages/4_output_parsed.py",
        "color": "#96CEB4"
    },
    {
        "icon": "📊",
        "title": "Clustering & Visualisasi",
        "desc": "Analisis segmentasi nasabah & grafik",
        "page": "pages/5_clustering.py",
        "color": "#FFEAA7"
    },
    {
        "icon": "🗑️",
        "title": "Hapus Semua Data",
        "desc": "Reset dan bersihkan semua data",
        "page": "pages/6_hapus_data.py",
        "color": "#DFE6E9"
    }
]

# Tampilkan menu dalam 2 kolom
for i in range(0, len(menu_items), 2):
    cols = st.columns(2)
    
    for idx, col in enumerate(cols):
        if i + idx < len(menu_items):
            item = menu_items[i + idx]
            
            with col:
                # Container untuk setiap menu
                with st.container():
                    st.markdown(f"""
                    <div style="
                        padding: 20px;
                        border-radius: 10px;
                        border-left: 5px solid {item['color']};
                        background-color: rgba(255, 255, 255, 0.05);
                        margin-bottom: 10px;
                    ">
                        <h3>{item['icon']} {item['title']}</h3>
                        <p style="color: #888;">{item['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Tombol navigasi
                    if st.button(
                        f"Buka {item['title']}", 
                        key=f"btn_{i}_{idx}",
                        use_container_width=True
                    ):
                        st.switch_page(item['page'])

st.divider()

# Workflow Section
st.markdown("## 🔄 Alur Kerja Sistem")

workflow_cols = st.columns(6)

workflow_steps = [
    ("1️⃣", "Upload\nPDF"),
    ("2️⃣", "Template\nPesan"),
    ("3️⃣", "Run\nPipeline"),
    ("4️⃣", "Cek\nOutput"),
    ("5️⃣", "Lihat\nClustering"),
]

for col, (num, step) in zip(workflow_cols, workflow_steps):
    with col:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px;">
            <div style="font-size: 2em;">{num}</div>
            <div style="font-size: 0.9em; white-space: pre-line;">{step}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Footer
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📊 Status Sistem")
    st.success("✅ Sistem Siap Digunakan")

with col2:
    st.markdown("### 🎯 Fitur Utama")
    st.markdown("""
    - OCR Otomatis
    - K-Means Clustering
    - Export CSV/Excel
    """)

with col3:
    st.markdown("### 💡 Bantuan")
    st.info("Gunakan menu di atas untuk navigasi atau klik tombol **Mulai** untuk upload dokumen")

