import re
import os
import pandas as pd

# === Helper umum ===
def normalize_number(num_str):
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
    r"s\.os\.?|m\.os\.?|s\.gz\.?|s\.t\.?|m\.ak\.?|apt\.?|sp\.[a-z]*|spt|"
    r"[A-Z]\s+[A-Z]{1,3}"  # pola seperti M TI
    r")\b",
    flags=re.IGNORECASE
)

    text = pattern.sub("", text)
    # rapikan spasi dan tanda baca
    text = re.sub(r"[\"'“”‘’,.;:-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text.upper()


# === Jatuh Tempo Extractor ===
def extract_no_sbg(text):
    digits = re.findall(r"\d", str(text))
    return "".join(digits[:16]) if len(digits) >= 16 else None


def extract_hp(text):
    match = re.search(r"\b08\d{7,13}\b", str(text))
    return match.group(0) if match else None


def extract_nasabah_jt(text):
    text = str(text)
    no_sbg = extract_no_sbg(text)
    hp = extract_hp(text)
    if no_sbg and hp:
        pattern = re.escape(no_sbg) + r"(.*?)" + re.escape(hp)
        m = re.search(pattern, text)
        if m:
            nama = m.group(1)

            # hapus prefix "B3" dan "KT" di awal nama
            nama = re.sub(r"^\s*B3\s*", "", nama, flags=re.IGNORECASE)
            nama = re.sub(r"^\s*KT\s*", "", nama, flags=re.IGNORECASE)

            return normalize_name(nama)
    return ""


def extract_tgl_jt(text):
    dates = re.findall(r"\d{2}-\d{2}-\d{4}", str(text))
    return dates[-1] if dates else None


def extract_uang_pinjaman_jt(text):
    numbers = re.findall(r"\d{1,3}(?:\.\d{3})+", str(text))
    if len(numbers) >= 2:
        return normalize_number(numbers[1])  # ambil angka kedua
    return None

def process_jatuh_tempo(df):
    df["NO_SBG"] = df["raw_text"].apply(extract_no_sbg)
    df["NASABAH"] = df["raw_text"].apply(extract_nasabah_jt)
    df["TELP_HP"] = df["raw_text"].apply(extract_hp)
    df["TGL_JATUH_TEMPO"] = df["raw_text"].apply(extract_tgl_jt)
    df["UANG_PINJAMAN"] = df["raw_text"].apply(extract_uang_pinjaman_jt)

    # drop record kosong (tanpa no_sbg atau nama nasabah)
    df = df[df["NO_SBG"].notna() & df["NO_SBG"].str.strip().ne("")]
    df = df[df["NASABAH"].str.strip().ne("")]

    return df[["NO_SBG", "NASABAH", "TGL_JATUH_TEMPO", "UANG_PINJAMAN", "TELP_HP"]]


# === Kredit Bermasalah Extractor ===
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
    df["NO_KREDIT"] = df["raw_text"].apply(extract_no_kredit)
    df["NASABAH"] = df["raw_text"].apply(extract_nasabah_kb)
    df["UANG_PINJAMAN"] = df["raw_text"].apply(extract_uang_pinjaman_kb)

    # drop record kosong (tanpa no_kredit atau nama nasabah)
    df = df[df["NO_KREDIT"].notna() & df["NO_KREDIT"].str.strip().ne("")]
    df = df[df["NASABAH"].str.strip().ne("")]

    return df[["NO_KREDIT", "NASABAH", "UANG_PINJAMAN"]]


# === Runner ===
def run_postprocessing(input_csv, output_csv):
    df = pd.read_csv(input_csv, encoding="utf-8-sig", dtype=str)

    if "jatuh_tempo" in os.path.basename(input_csv):
        df_out = process_jatuh_tempo(df)
    else:
        df_out = process_kredit_bermasalah(df)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_out.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"[INFO] Hasil disimpan → {output_csv}")
    return df_out


def latest_csv(prefix, raw_dir):
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
        df_out = run_postprocessing(f, out_path)  # panggil fungsi yang asli
        results[prefix] = out_path

    return results


if __name__ == "__main__":
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
