import streamlit as st
import json, os, time

st.title("Template Message")
st.markdown("### Langkah 2: Buat Template Pesan untuk Nasabah")

template_path = os.path.join("config", "templates.json")

# Load existing templates
if os.path.exists(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        templates = json.load(f)
else:
    os.makedirs("config", exist_ok=True)
    templates = {"jatuh_tempo": "", "kredit_bermasalah": ""}

# Info box
with st.expander("ℹ️ Panduan Template Message"):
    st.markdown("""
    **Cara Menggunakan:**
    1. Pilih tipe dokumen (Jatuh Tempo / Kredit Bermasalah)
    2. Klik tombol variabel untuk menambahkan ke template
    3. Ketik pesan Anda dengan variabel yang dipilih
    4. Klik "Simpan Template" untuk menyimpan
    
    **Variabel yang Tersedia:**
    - **{NO_SBG}** / **{NO_KREDIT}**: Nomor kredit/SBG
    - **{NASABAH}**: Nama nasabah
    - **{TGL_JATUH_TEMPO}**: Tanggal jatuh tempo (khusus jatuh tempo)
    - **{UANG_PINJAMAN}**: Jumlah pinjaman
    
    **Contoh Template:**
    ```
    Yth. {NASABAH},
    Kami ingatkan bahwa pinjaman Anda senilai {UANG_PINJAMAN} 
    akan jatuh tempo pada {TGL_JATUH_TEMPO}.
    Terima kasih.
    ```
    """)

# Select document type
doc_type = st.selectbox(
    "Pilih Tipe Dokumen", 
    ["jatuh tempo", "kredit bermasalah"],
    help="Pilih sesuai dengan dokumen yang telah diupload"
)

# Placeholder tombol variabel
placeholders = {
    "jatuh tempo": ["{NO_SBG}", "{NASABAH}", "{TGL_JATUH_TEMPO}", "{UANG_PINJAMAN}"],
    "kredit bermasalah": ["{NO_KREDIT}", "{NASABAH}", "{UANG_PINJAMAN}"]
}

# Initialize session state
if "custom_text" not in st.session_state:
    st.session_state.custom_text = templates.get(doc_type.replace(" ", "_"), "")

# Update session state when doc_type changes
current_template = templates.get(doc_type.replace(" ", "_"), "")
if st.session_state.get("last_doc_type") != doc_type:
    st.session_state.custom_text = current_template
    st.session_state.last_doc_type = doc_type

st.markdown("###Variabel Template")
st.caption("Klik tombol variabel untuk menambahkan ke template")

# Buttons untuk placeholder
cols = st.columns(4)
for i, ph in enumerate(placeholders[doc_type]):
    with cols[i % 4]:
        if st.button(ph, key=f"btn_{ph}", use_container_width=True):
            st.session_state.custom_text += ph + " "
            st.rerun()

st.markdown("###Template Pesan")

# Text area untuk template
st.session_state.custom_text = st.text_area(
    "Ketik template pesan Anda di bawah ini:",
    st.session_state.custom_text,
    height=250,
    help="Gunakan variabel di atas untuk membuat template dinamis"
)

# Preview template
if st.session_state.custom_text.strip():
    with st.expander("Preview Template"):
        st.markdown("**Contoh dengan data dummy:**")
        preview_text = st.session_state.custom_text
        preview_text = preview_text.replace("{NO_SBG}", "12345")
        preview_text = preview_text.replace("{NO_KREDIT}", "KR-67890")
        preview_text = preview_text.replace("{NASABAH}", "Budi Santoso")
        preview_text = preview_text.replace("{TGL_JATUH_TEMPO}", "31 Desember 2024")
        preview_text = preview_text.replace("{UANG_PINJAMAN}", "Rp 5.000.000")
        st.info(preview_text)

st.divider()

# Action buttons
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("💾 Simpan Template", type="primary", use_container_width=True):
        if not st.session_state.custom_text.strip():
            st.error("⚠️ Template tidak boleh kosong!")
        else:
            with st.spinner("Menyimpan template..."):
                templates[doc_type.replace(" ", "_")] = st.session_state.custom_text
                
                # Ensure config directory exists
                os.makedirs("config", exist_ok=True)
                
                with open(template_path, "w", encoding="utf-8") as f:
                    json.dump(templates, f, indent=2, ensure_ascii=False)
                
                st.success(f"✅ Template untuk {doc_type} berhasil disimpan!")
                time.sleep(1)
                
                # Auto redirect
                st.info("🔄 Mengarahkan ke halaman Pipeline (OCR)...")
                time.sleep(1)
                st.switch_page("pages/3_jalankan_ocr.py")

with col2:
    if st.button("⏭️ Lanjut ke Pipeline (OCR)", use_container_width=True):
        st.info("🔄 Mengarahkan ke halaman Pipeline...")
        time.sleep(0.5)
        st.switch_page("pages/3_jalankan_ocr.py")

st.divider()

# Show existing templates
st.markdown("### 📚 Template Tersimpan")

with st.expander("Lihat semua template yang tersimpan"):
    for key, value in templates.items():
        st.markdown(f"**{key.replace('_', ' ').title()}:**")
        if value.strip():
            st.code(value, language="text")
        else:
            st.caption("_Template belum dibuat_")
        st.markdown("---")

# Tips
st.caption("💡 **Tip:** Template yang disimpan akan digunakan saat generate pesan untuk nasabah")