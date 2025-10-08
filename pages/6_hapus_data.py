import streamlit as st
import os

st.title("⚠️ Hapus Semua Data")

def hapus_semua_data():
    deleted_count = 0
    for folder in ["dataset", "images", "output"]:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.endswith(".pkl") or f == ".gitkeep":
                        continue
                    try:
                        os.remove(os.path.join(root, f))
                        deleted_count += 1
                    except:
                        pass
    return deleted_count

if st.button("Hapus Semua Data"):
    count = hapus_semua_data()
    st.success(f"{count} file berhasil dihapus. Model tetap aman.")
