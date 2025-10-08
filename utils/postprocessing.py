import re
import os
import pandas as pd

# === Helper umum ===
def normalize_number(num_str):
    """Bersihkan angka dari karakter non-digit."""
    if pd.isna(num_str) or str(num_str).strip() == "":
        return None
    clean = re.sub(r"[^\d]", "", str(num_str))
    return int(clean) if clean else None


def normalize_name(value: str) -> str:
    """Bersihkan nama nasabah dari gelar/akronim dan kapitalisasi."""
    if not value or pd.isna(value):
        return ""
    text = str(value)

    # hapus kode/gelar umum
    pattern = re.compile(
        r"\b("
        r"dr\.?|drs\.?|dr_?|prof\.?|ir\.?|h\.?|kh\.?|tgk\.?|r\.?|hr\.?|se\.?|kt\.?|mm\.?|s\.e\.?|m\.m\.?|"
        r"s\.farm\.?|m\.farm\.?|s\.ked\.?|s\.kom\.?|m\.kom\.?|s\.si\.?|m\.si\.?|s\.pd\.?|m\.pd\.?|"
        r"s\.os\.?|m\.os\.?|s\.gz\.?|s\.t\.?|m\.ak\.?|apt\.?|sp\.[a-z]*|spt|spd|"
        r"[A-Z]\s+[A-Z]{1,3}"  # pola seperti M TI
        r")\b",
        flags=re.IGNORECASE
    )

    text = pattern.sub("", text)
    # rapikan spasi dan tanda baca
    text = re.sub(r"[\"',.;:-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text.upper()


def extract_first_phone(phone_str):
    """Ambil hanya nomor telepon pertama jika ada lebih dari satu."""
    if pd.isna(phone_str) or str(phone_str).strip() == "":
        return None
    
    phone_str = str(phone_str).strip()
    # Split berdasarkan semicolon atau koma
    phones = re.split(r'[;,]', phone_str)
    
    # Ambil nomor pertama dan bersihkan
    first_phone = phones[0].strip()
    
    # Validasi format nomor HP (08 diikuti 8-13 digit)
    match = re.search(r'\b08\d{8,13}\b', first_phone)
    if match:
        return match.group(0)
    
    return first_phone if first_phone else None


def process_jatuh_tempo(df):
    """Proses data jatuh tempo dari CSV yang sudah terstruktur."""
    
    # Ekstrak kolom yang dibutuhkan
    df_out = pd.DataFrame()
    
    # No_SBG - pastikan formatnya string dan bersih
    df_out["NO_SBG"] = df["No_SBG"].astype(str).str.strip()
    
    # Nasabah - bersihkan nama dari gelar
    df_out["NASABAH"] = df["Nasabah"].apply(normalize_name)
    
    # Telp_HP - ambil hanya nomor pertama
    df_out["TELP_HP"] = df["Telp_HP"].apply(extract_first_phone)
    
    # Tgl_Jatuh_Tempo - format tanggal
    df_out["TGL_JATUH_TEMPO"] = df["Tgl_Jatuh_Tempo"].astype(str).str.strip()
    
    # Uang_Pinjaman - convert ke integer
    df_out["UANG_PINJAMAN"] = df["Uang_Pinjaman"].apply(normalize_number)
    
    # Drop record kosong (tanpa no_sbg atau nama nasabah)
    df_out = df_out[df_out["NO_SBG"].notna() & df_out["NO_SBG"].ne("")]
    df_out = df_out[df_out["NASABAH"].str.strip().ne("")]
    
    return df_out[["NO_SBG", "NASABAH", "TELP_HP", "TGL_JATUH_TEMPO", "UANG_PINJAMAN"]]


# === Kredit Bermasalah Extractor (tetap untuk backward compatibility) ===
def extract_no_kredit(text: str):
    text = str(text)
    digits = re.findall(r"\d", text)
    if len(digits) < 16:
        return None
    base = "".join(digits[:16])
    m = re.search(r"\d{16}\D*(\d{2})\s*\d{6,12}", text)
    if m:
        return base + m.group(1)
    return base


def extract_nasabah_kb(text: str):
    text = str(text)
    text = re.sub(r"^\D*(\d\D*){16}", "", text)  # hapus 16 digit pertama
    text = re.sub(r"^\s*\d{2}\s*\d{6,12}\s*", "", text)  # hapus kode + CIF
    parts = re.split(r"\d{2}-\d{2}-\d{4}", text, maxsplit=1)
    nama = parts[0].strip() if parts else text
    return normalize_name(nama)


def extract_uang_pinjaman_kb(text: str):
    dates = re.findall(r"\d{2}-\d{2}-\d{4}", str(text))
    if len(dates) < 2:
        return None
    cutoff_pos = text.find(dates[1])
    after_cutoff = text[cutoff_pos + len(dates[1]):]
    match = re.search(r"\d{1,3}(?:\.\d{3})+", after_cutoff)
    if match:
        return normalize_number(match.group(0))
    return None


def process_kredit_bermasalah(df: pd.DataFrame):
    """Proses data kredit bermasalah."""
    
    # Cek apakah data sudah terstruktur (ada kolom) atau masih raw_text
    if "raw_text" in df.columns:
        # Format lama (raw OCR)
        df["NO_KREDIT"] = df["raw_text"].apply(extract_no_kredit)
        df["NASABAH"] = df["raw_text"].apply(extract_nasabah_kb)
        df["UANG_PINJAMAN"] = df["raw_text"].apply(extract_uang_pinjaman_kb)
    else:
        # Format baru (sudah terstruktur)
        df_out = pd.DataFrame()
        df_out["NO_KREDIT"] = df.get("No_Kredit", df.get("No_SBG", "")).astype(str).str.strip()
        df_out["NASABAH"] = df["Nasabah"].apply(normalize_name)
        df_out["UANG_PINJAMAN"] = df["Uang_Pinjaman"].apply(normalize_number)
        
        # Drop record kosong
        df_out = df_out[df_out["NO_KREDIT"].notna() & df_out["NO_KREDIT"].ne("")]
        df_out = df_out[df_out["NASABAH"].str.strip().ne("")]
        
        return df_out[["NO_KREDIT", "NASABAH", "UANG_PINJAMAN"]]

    # drop record kosong (tanpa no_kredit atau nama nasabah)
    df = df[df["NO_KREDIT"].notna() & df["NO_KREDIT"].str.strip().ne("")]
    df = df[df["NASABAH"].str.strip().ne("")]

    return df[["NO_KREDIT", "NASABAH", "UANG_PINJAMAN"]]


# === Runner ===
def run_postprocessing(input_csv, output_csv):
    """Jalankan postprocessing pada file CSV."""
    
    df = pd.read_csv(input_csv, encoding="utf-8-sig", dtype=str)
    
    # Deteksi tipe data berdasarkan nama file atau kolom
    if "jatuh_tempo" in os.path.basename(input_csv).lower() or "Tgl_Jatuh_Tempo" in df.columns:
        df_out = process_jatuh_tempo(df)
    else:
        df_out = process_kredit_bermasalah(df)
    
    # Simpan hasil
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_out.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"[INFO] Hasil disimpan → {output_csv}")
    print(f"[INFO] Total record: {len(df_out)}")
    
    return df_out


def latest_csv(prefix, raw_dir):
    """Cari file CSV terbaru berdasarkan prefix."""
    files = [
        os.path.join(raw_dir, f)
        for f in os.listdir(raw_dir)
        if f.startswith(prefix) and f.endswith(".csv")
    ]
    return max(files, key=os.path.getmtime) if files else None


def run_postprocessing_wrapper(base_output_dir):
    """
    Wrapper agar pipeline cukup kasih OUTPUT_DIR.
    Akan cari file terbaru hasil OCR, lalu postprocess dan simpan hasilnya.
    """
    raw_dir = os.path.join(base_output_dir, "raw_ocr")
    out_dir = os.path.join(base_output_dir, "postprocessed")
    os.makedirs(out_dir, exist_ok=True)

    results = {}
    for prefix in ("jatuh_tempo", "kredit_bermasalah"):
        f = latest_csv(prefix, raw_dir)
        if not f:
            print(f"[WARN] Tidak ada file {prefix} di {raw_dir}")
            continue
        out_name = os.path.basename(f).replace("raw", "final")
        out_path = os.path.join(out_dir, out_name)
        df_out = run_postprocessing(f, out_path)
        results[prefix] = out_path

    return results


if __name__ == "__main__":
    # Contoh penggunaan langsung
    RAW_DIR = os.path.join("output", "raw_ocr")
    OUT_DIR = os.path.join("output", "postprocessed")
    os.makedirs(OUT_DIR, exist_ok=True)

    for prefix in ("jatuh_tempo", "kredit_bermasalah"):
        f = latest_csv(prefix, RAW_DIR)
        if not f:
            print(f"[WARN] Tidak ada file {prefix} di {RAW_DIR}")
            continue
        out_name = os.path.basename(f).replace("raw", "final")
        out_path = os.path.join(OUT_DIR, out_name)
        run_postprocessing(f, out_path)