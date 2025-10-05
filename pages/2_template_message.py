import streamlit as st
import json, os, time

st.title("📝 Template Message")

template_path = os.path.join("config", "templates.json")
if os.path.exists(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        templates = json.load(f)
else:
    templates = {"jatuh_tempo": "", "kredit_bermasalah": ""}

doc_type = st.selectbox("Pilih Tipe Dokumen", ["jatuh tempo", "kredit bermasalah"])

# Placeholder tombol variabel
placeholders = {
    "jatuh tempo": ["{NO_SBG}", "{NASABAH}", "{TGL_JATUH_TEMPO}", "{UANG_PINJAMAN}"],
    "kredit bermasalah": ["{NO_KREDIT}", "{NASABAH}", "{UANG_PINJAMAN}"]
}

if "custom_text" not in st.session_state:
    st.session_state.custom_text = templates.get(doc_type.replace(" ", "_"), "")

cols = st.columns(4)
for i, ph in enumerate(placeholders[doc_type]):
    if cols[i % 4].button(ph, key=f"btn_{ph}"):
        st.session_state.custom_text += ph + " "

st.session_state.custom_text = st.text_area("Template Pesan",
                                            st.session_state.custom_text,
                                            height=200)

if st.button("💾 Simpan Template"):
    templates[doc_type.replace(" ", "_")] = st.session_state.custom_text
    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)
    st.success(f"Template untuk {doc_type} berhasil disimpan!")
