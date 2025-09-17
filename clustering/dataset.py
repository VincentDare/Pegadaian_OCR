import pandas as pd
import os

# --- Base Path ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_PARSED_DIR = os.path.join(BASE_DIR, "output", "parsed_output")
OUTPUT_DATASET_DIR = os.path.join(BASE_DIR, "output", "dataset_clustering")

# Pastikan folder dataset_clustering ada
os.makedirs(OUTPUT_DATASET_DIR, exist_ok=True)

DATASET_PATH = os.path.join(OUTPUT_DATASET_DIR, "dataset.csv")

def build_dataset():
    """
    Gabungkan jatuh tempo & kredit bermasalah jadi 1 dataset.csv
    Disimpan di output/dataset_clustering/dataset.csv
    """
    files = [f for f in os.listdir(OUTPUT_PARSED_DIR) if f.endswith(".csv")]

    # Filter file jatuh tempo dan kredit bermasalah
    jatuh = [f for f in files if "jatuh_tempo" in f]
    kredit = [f for f in files if "kredit_bermasalah" in f]

    df_list = []
    if jatuh:
        jatuh_path = os.path.join(OUTPUT_PARSED_DIR, jatuh[-1])  # ambil terbaru
        print(f"[INFO] Tambah jatuh_tempo: {jatuh_path}")
        df_list.append(pd.read_csv(jatuh_path))
    if kredit:
        kredit_path = os.path.join(OUTPUT_PARSED_DIR, kredit[-1])
        print(f"[INFO] Tambah kredit_bermasalah: {kredit_path}")
        df_list.append(pd.read_csv(kredit_path))

    if not df_list:
        raise FileNotFoundError("❌ Tidak ada file parsed ditemukan untuk dataset.")

    df = pd.concat(df_list, ignore_index=True)
    df.to_csv(DATASET_PATH, index=False)
    print(f"✅ Dataset gabungan disimpan di {DATASET_PATH}")
    return df

def load_dataset():
    """
    Load dataset.csv langsung dari dataset_clustering.
    """
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError("❌ Dataset belum dibuat. Jalankan build_dataset() dulu.")
    return pd.read_csv(DATASET_PATH)

def run_dataset():
    """
    Runner untuk pipeline
    """
    if not os.path.exists(DATASET_PATH):
        df = build_dataset()
    else:
        df = load_dataset()
    print(f"✅ Dataset berhasil dimuat. Jumlah baris: {len(df)}")
    return df

if __name__ == "__main__":
    df = run_dataset()
    print(df.head())
