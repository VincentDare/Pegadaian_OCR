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
    df = pd.read_csv(dataset_path, dtype=str)

    # Normalisasi nama kolom ke uppercase
    df.columns = [c.upper() for c in df.columns]

    print(f"[INFO] Kolom awal: {df.columns.tolist()}")

    # === UNIFIKASI KOLOM ===
    # 1. Unifikasi NO_KREDIT → NO_SBG (untuk kredit bermasalah)
    if "NO_KREDIT" in df.columns and "NO_SBG" not in df.columns:
        df.rename(columns={"NO_KREDIT": "NO_SBG"}, inplace=True)
        print("[INFO] Kolom NO_KREDIT diubah menjadi NO_SBG")
    elif "NO_KREDIT" in df.columns and "NO_SBG" in df.columns:
        # Jika ada keduanya, merge ke NO_SBG
        df["NO_SBG"] = df["NO_SBG"].fillna(df["NO_KREDIT"])
        df.drop(columns=["NO_KREDIT"], inplace=True)
        print("[INFO] Kolom NO_KREDIT digabung ke NO_SBG")

    # 2. Unifikasi TGL_KREDIT → TGL_JATUH_TEMPO (untuk kredit bermasalah)
    if "TGL_KREDIT" in df.columns and "TGL_JATUH_TEMPO" not in df.columns:
        df.rename(columns={"TGL_KREDIT": "TGL_JATUH_TEMPO"}, inplace=True)
        print("[INFO] Kolom TGL_KREDIT diubah menjadi TGL_JATUH_TEMPO")
    elif "TGL_KREDIT" in df.columns and "TGL_JATUH_TEMPO" in df.columns:
        # Jika ada keduanya, merge ke TGL_JATUH_TEMPO
        df["TGL_JATUH_TEMPO"] = df["TGL_JATUH_TEMPO"].fillna(df["TGL_KREDIT"])
        df.drop(columns=["TGL_KREDIT"], inplace=True)
        print("[INFO] Kolom TGL_KREDIT digabung ke TGL_JATUH_TEMPO")

    # Support variasi nama kolom tanggal lain
    if "TANGGAL_JATUH_TEMPO" in df.columns and "TGL_JATUH_TEMPO" not in df.columns:
        df.rename(columns={"TANGGAL_JATUH_TEMPO": "TGL_JATUH_TEMPO"}, inplace=True)
    if "TANGGAL_KREDIT" in df.columns and "TGL_JATUH_TEMPO" not in df.columns:
        df.rename(columns={"TANGGAL_KREDIT": "TGL_JATUH_TEMPO"}, inplace=True)

    # === HAPUS KOLOM TELP_HP ===
    telp_columns = [c for c in df.columns if "TELP" in c or "HP" in c or "PHONE" in c]
    if telp_columns:
        df.drop(columns=telp_columns, inplace=True)
        print(f"[INFO] Kolom telepon dihapus: {telp_columns}")

    print(f"[INFO] Kolom setelah unifikasi: {df.columns.tolist()}")

    # === VALIDASI KOLOM WAJIB ===
    required_cols = ["NO_SBG", "NASABAH", "UANG_PINJAMAN"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(
                f"❌ Kolom {col} tidak ditemukan di dataset! "
                f"Kolom tersedia: {df.columns.tolist()}"
            )

    # Ambil kolom yang dibutuhkan (termasuk tanggal jika ada)
    selected_cols = required_cols.copy()
    if "TGL_JATUH_TEMPO" in df.columns:
        selected_cols.append("TGL_JATUH_TEMPO")
        print("[INFO] Kolom TGL_JATUH_TEMPO disimpan untuk analisis")

    df = df[selected_cols].copy()

    # === CLEANING DATA ===
    # 1. Bersihkan UANG_PINJAMAN
    df["UANG_PINJAMAN"] = (
        df["UANG_PINJAMAN"]
        .astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .replace("", "0")
        .astype(float)
    )

    # 2. Drop rows dengan UANG_PINJAMAN = 0 atau kosong
    df = df[df["UANG_PINJAMAN"] > 0]
    print(f"[INFO] Total record setelah cleaning: {len(df)}")

    # 3. Drop rows dengan NO_SBG atau NASABAH kosong
    df = df[df["NO_SBG"].notna() & (df["NO_SBG"].str.strip() != "")]
    df = df[df["NASABAH"].notna() & (df["NASABAH"].str.strip() != "")]

    # === SCALING ===
    scaler = StandardScaler()
    df["PINJAMAN_SCALED"] = scaler.fit_transform(df[["UANG_PINJAMAN"]])

    # === SIMPAN HASIL ===
    # 1. Simpan hasil preprocessing
    out_path = os.path.join(PREPROCESS_DIR, "preprocessed.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    # 2. Simpan scaler
    scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
    joblib.dump(scaler, scaler_path)

    print(f"\n✅ Preprocessing selesai!")
    print(f"📂 File disimpan di: {out_path}")
    print(f"📦 Scaler disimpan di: {scaler_path}")
    print(f"📊 Total record: {len(df)}")
    print(f"📋 Kolom final: {df.columns.tolist()}")
    print(f"\n📄 Preview data:")
    print(df.head(10))
    
    # Statistik deskriptif
    print(f"\n📈 Statistik UANG_PINJAMAN:")
    print(df["UANG_PINJAMAN"].describe())

    return df

if __name__ == "__main__":
    run_preprocessing()