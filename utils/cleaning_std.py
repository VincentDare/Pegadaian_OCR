# utils/cleaning_std.py
import re
import pandas as pd
from datetime import datetime
import os, glob, unicodedata

# ---- Normalisasi uang ----
def normalize_rupiah(value: str):
    if not value or pd.isna(value):
        return None

    raw = str(value).strip()
    cleaned = re.sub(r"[^\d.,]", "", raw)
    if not cleaned:
        return None

    digits = re.sub(r"[^\d]", "", cleaned)

    # OCR salah format (contoh: 176,104) → buang
    if re.match(r"^\d{1,3},\d{3}$", cleaned):
        return None

    # Angka kecil (< 100.000) buang
    if digits.isdigit() and int(digits) < 100000:
        return None

    try:
        return int(digits)
    except ValueError:
        return None


# ---- Normalisasi tanggal ----
def normalize_date(value: str) -> str:
    if not value or pd.isna(value):
        return ""
    value = str(value).strip()

    fmts = [
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%d-%m-%y", "%d/%m/%y", "%Y-%m-%d",
        "%d-%b-%Y", "%d-%b-%y", "%d %B %Y", "%d %b %Y"
    ]

    for fmt in fmts:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%d-%m-%Y")
        except ValueError:
            continue
    return value


# ---- Normalisasi nama (UPPERCASE, hapus gelar) ----
def normalize_name(value: str) -> str:
    if not value or pd.isna(value):
        return ""

    text = str(value)

    # normalisasi unicode biar kutip miring = kutip biasa
    text = unicodedata.normalize("NFKC", text)

    # hapus semua jenis kutip (", ', ', ", ")
    text = re.sub(r"[\"'""'']", " ", text)

    # hapus gelar akademik dan profesional
    pattern = re.compile(
        r"\b("
        r"dr\.?|drs\.?|dr_?|prof\.?|ir\.?|h\.?|kh\.?|tgk\.?|r\.?|hr\.?|se\.?|kt\.?|mm\.?|"
        r"s\.e\.?|m\.m\.?|s\.farm\.?|m\.farm\.?|s\.ked\.?|s\.kom\.?|m\.kom\.?|"
        r"s\.si\.?|m\.si\.?|s\.pd\.?|m\.pd\.?|s\.os\.?|m\.os\.?|s\.gz\.?|s\.t\.?|"
        r"m\.ak\.?|apt\.?|sp\.[a-z]*|spt|spd"
        r")\b",
        flags=re.IGNORECASE
    )
    text = pattern.sub("", text)

    # hapus tanda baca aneh ; : , . - yang nempel
    text = re.sub(r"[;:,\.\-]+", " ", text)

    # rapikan spasi
    text = re.sub(r"\s+", " ", text).strip()

    # UPPERCASE (sesuai output postprocessing)
    return text.upper()


# ---- Normalisasi nomor (SBG/Kredit) ----
def normalize_number(value: str) -> str:
    if not value or pd.isna(value):
        return ""
    return re.sub(r"[^\d]", "", str(value))


# ---- Normalisasi nomor HP ----
def normalize_hp(value: str) -> str:
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()
    value = re.sub(r"[^\d]", "", value)  # hanya angka

    # ubah format 62xxx → 08xxx
    if value.startswith("62"):
        value = "0" + value[2:]

    # syarat minimal 9 digit, maksimal 13 digit
    if 9 <= len(value) <= 13 and value.startswith("0"):
        return value

    return value  # fallback: simpan apa adanya


# ---- Main Cleaner ----
def clean_dataframe(df: pd.DataFrame, doc_type: str) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    
    # Normalisasi nama kolom ke lowercase untuk konsistensi
    df.columns = df.columns.str.lower()

    # Cleaning untuk nama nasabah
    if "nasabah" in df.columns:
        df["nasabah"] = df["nasabah"].apply(normalize_name)

    # Cleaning untuk uang pinjaman
    if "uang_pinjaman" in df.columns:
        df["uang_pinjaman"] = df["uang_pinjaman"].apply(normalize_rupiah)

    # Cleaning untuk nomor SBG/Kredit
    if "no_sbg" in df.columns:
        df["no_sbg"] = df["no_sbg"].apply(normalize_number)
    if "no_kredit" in df.columns:
        df["no_kredit"] = df["no_kredit"].apply(normalize_number)

    # Cleaning untuk tanggal
    date_col = None
    if doc_type == "jatuh_tempo":
        if "tgl_jatuh_tempo" in df.columns:
            df["tgl_jatuh_tempo"] = df["tgl_jatuh_tempo"].apply(normalize_date)
            date_col = "tgl_jatuh_tempo"
        elif "tanggal_jatuh_tempo" in df.columns:
            df["tanggal_jatuh_tempo"] = df["tanggal_jatuh_tempo"].apply(normalize_date)
            date_col = "tanggal_jatuh_tempo"
    elif doc_type == "kredit_bermasalah":
        if "tgl_kredit" in df.columns:
            df["tgl_kredit"] = df["tgl_kredit"].apply(normalize_date)
            date_col = "tgl_kredit"
        elif "tanggal_kredit" in df.columns:
            df["tanggal_kredit"] = df["tanggal_kredit"].apply(normalize_date)
            date_col = "tanggal_kredit"

    # Cleaning untuk nomor HP
    if "telp_hp" in df.columns:
        df["telp_hp"] = df["telp_hp"].apply(normalize_hp)

    # Drop rows dengan data penting kosong
    if "nasabah" in df.columns:
        df = df[df["nasabah"].notna() & (df["nasabah"].str.strip() != "")]
    
    if "no_sbg" in df.columns:
        df = df[df["no_sbg"].notna() & (df["no_sbg"].str.strip() != "")]
    elif "no_kredit" in df.columns:
        df = df[df["no_kredit"].notna() & (df["no_kredit"].str.strip() != "")]

    # SORTING: Urutkan berdasarkan tanggal (ascending)
    if date_col and date_col in df.columns:
        # Buat kolom sementara untuk sorting (convert ke datetime)
        df["_sort_date"] = pd.to_datetime(
            df[date_col], 
            format="%d-%m-%Y", 
            errors="coerce"
        )
        # Sort berdasarkan tanggal
        df = df.sort_values("_sort_date", ascending=True)
        # Hapus kolom sementara
        df = df.drop(columns=["_sort_date"])
        # Reset index
        df = df.reset_index(drop=True)

    return df


def run_cleaning(base_output_dir: str):
    """
    Jalankan cleaning untuk semua file postprocessed.
    Output disimpan ke output/cleaned.
    """
    raw_dir = os.path.join(base_output_dir, "postprocessed")
    out_dir = os.path.join(base_output_dir, "cleaned")
    os.makedirs(out_dir, exist_ok=True)

    raw_files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    if not raw_files:
        print("[WARN] Tidak ada file postprocessed ditemukan.")
        return {}

    results = {}
    for f in raw_files:
        if "jatuh_tempo" in os.path.basename(f):
            doc_type = "jatuh_tempo"
        elif "kredit_bermasalah" in os.path.basename(f):
            doc_type = "kredit_bermasalah"
        else:
            continue

        # Force baca semua sebagai string agar telp_hp tidak hilang
        df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
        
        print(f"[INFO] Processing {os.path.basename(f)} - {len(df)} rows")
        
        df_clean = clean_dataframe(df, doc_type)

        # Pastikan uang_pinjaman integer
        if "uang_pinjaman" in df_clean.columns:
            df_clean["uang_pinjaman"] = pd.to_numeric(
                df_clean["uang_pinjaman"], errors="coerce"
            ).astype("Int64")

        out_name = os.path.basename(f).replace("final", "clean")
        out_path = os.path.join(out_dir, out_name)
        df_clean.to_csv(out_path, index=False, encoding="utf-8-sig")
        
        print(f"[INFO] Hasil cleaning {doc_type} disimpan → {out_path}")
        print(f"[INFO] Total record setelah cleaning: {len(df_clean)}")
        print(f"[INFO] Data telah diurutkan berdasarkan tanggal (ascending)")
        
        results[doc_type] = out_path

    return results


# ---- Runner ----
if __name__ == "__main__":
    RAW_DIR = os.path.join("output", "postprocessed")
    OUT_DIR = os.path.join("output", "cleaned")
    os.makedirs(OUT_DIR, exist_ok=True)

    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not raw_files:
        print("[WARN] Tidak ada file postprocessed ditemukan.")
    else:
        for f in raw_files:
            if "jatuh_tempo" in os.path.basename(f):
                doc_type = "jatuh_tempo"
            elif "kredit_bermasalah" in os.path.basename(f):
                doc_type = "kredit_bermasalah"
            else:
                continue

            # Force baca semua sebagai string agar telp_hp tidak hilang
            df = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
            
            print(f"[INFO] Processing {os.path.basename(f)} - {len(df)} rows")
            
            df_clean = clean_dataframe(df, doc_type)

            # Pastikan uang_pinjaman integer, bukan float
            if "uang_pinjaman" in df_clean.columns:
                df_clean["uang_pinjaman"] = pd.to_numeric(
                    df_clean["uang_pinjaman"], errors="coerce"
                ).astype("Int64")

            out_name = os.path.basename(f).replace("final", "clean")
            out_path = os.path.join(OUT_DIR, out_name)
            df_clean.to_csv(out_path, index=False, encoding="utf-8-sig")
            
            print(f"[INFO] Hasil cleaning {doc_type} disimpan → {out_path}")
            print(f"[INFO] Total record setelah cleaning: {len(df_clean)}")
            print(f"[INFO] Data telah diurutkan berdasarkan tanggal (ascending)")