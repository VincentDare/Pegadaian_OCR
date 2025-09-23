import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATASET_DIR = os.path.join(BASE_DIR, "output", "dataset_clustering")

# Folder output
PREPROCESS_DIR = os.path.join(BASE_DIR, "output", "clustering", "preprocessing")
MODEL_DIR = os.path.join(BASE_DIR, "output", "clustering", "model")

os.makedirs(PREPROCESS_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

def run_preprocessing():
    dataset_path = os.path.join(DATASET_DIR, "dataset.csv")
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"❌ File {dataset_path} tidak ditemukan!")

    # Load dataset
    df = pd.read_csv(dataset_path)

    # Normalisasi nama kolom ke uppercase
    df.columns = [c.upper() for c in df.columns]

# Akali kolom NO_KREDIT jadi NO_SBG (kalau ada)
    if "NO_KREDIT" in df.columns and "NO_SBG" not in df.columns:
        df.rename(columns={"NO_KREDIT": "NO_SBG"}, inplace=True)

    required_cols = ["NO_SBG", "NASABAH", "UANG_PINJAMAN"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"❌ Kolom {col} tidak ditemukan di dataset! Kolom tersedia: {df.columns.tolist()}")

    df = df[required_cols].copy()

    # Bersihkan UANG_PINJAMAN
    df["UANG_PINJAMAN"] = (
        df["UANG_PINJAMAN"]
        .astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .replace("", "0")
        .astype(float)
    )

    # Scaling
    scaler = StandardScaler()
    df["PINJAMAN_SCALED"] = scaler.fit_transform(df[["UANG_PINJAMAN"]])

    # Simpan hasil preprocessing
    out_path = os.path.join(PREPROCESS_DIR, "preprocessed.csv")
    df.to_csv(out_path, index=False)

    # Simpan scaler
    scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
    joblib.dump(scaler, scaler_path)

    print(f"✅ Preprocessing selesai.")
    print(f"📂 File disimpan di: {out_path}")
    print(f"📦 Scaler disimpan di: {scaler_path}")
    print(df.head())
    return df

if __name__ == "__main__":
    run_preprocessing()
