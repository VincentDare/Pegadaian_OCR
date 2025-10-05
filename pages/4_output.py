import streamlit as st
import os, pandas as pd

OUTPUT_DIR = "output"
parsed_dir = os.path.join(OUTPUT_DIR, "parsed_output")
messages_dir = os.path.join(OUTPUT_DIR, "messages")
missing_dir = os.path.join(OUTPUT_DIR, "missing")

st.title("📑 Output Parsed & Messages")

option = st.selectbox("Pilih Data", ["Parsed Document", "Missing Names", "Messages"])

if option == "Parsed Document":
    if os.path.exists(parsed_dir):
        files = [f for f in os.listdir(parsed_dir) if f.endswith("_extracted.csv")]
        if files:
            selected_file = st.selectbox("Pilih file parsed", files)
            df = pd.read_csv(os.path.join(parsed_dir, selected_file))
            st.dataframe(df.head(10))
        else:
            st.warning("Belum ada hasil parsed.")
elif option == "Missing Names":
    if os.path.exists(missing_dir):
        files = [f for f in os.listdir(missing_dir) if f.endswith(".csv")]
        if files:
            selected_file = st.selectbox("Pilih file missing", files)
            df = pd.read_csv(os.path.join(missing_dir, selected_file))
            st.dataframe(df.head(10))
        else:
            st.info("Tidak ada missing names.")
elif option == "Messages":
    if os.path.exists(messages_dir):
        files = [f for f in os.listdir(messages_dir) if f.endswith((".csv", ".xlsx"))]
        if files:
            selected_file = st.selectbox("Pilih file message", files)
            file_path = os.path.join(messages_dir, selected_file)
            df = pd.read_csv(file_path) if selected_file.endswith(".csv") else pd.read_excel(file_path)
            st.dataframe(df.head(10))
        else:
            st.info("Belum ada messages.")
