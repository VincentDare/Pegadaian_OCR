import os
import re
import datetime as dt
import pandas as pd
import easyocr
from tqdm import tqdm
import cv2
import pandas as pd
import datetime as dt

# === Folder input & output ===
IMAGES_DIR = "images"
OUTPUT_DIR = os.path.join("output", "raw_ocr")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_NAMES_LOG = os.path.join("output", "missing_names.csv")

# === Init EasyOCR ===
def get_reader():
    use_gpu = False
    try:
        import torch
        use_gpu = torch.cuda.is_available()
        if use_gpu:
            print(f"[INFO] GPU terdeteksi: {torch.cuda.get_device_name(0)}")
    except Exception:
        pass
    return easyocr.Reader(['id', 'en'], gpu=use_gpu)


def extract_text(reader, img_path: str) -> str:
    try:
        results = reader.readtext(img_path, detail=1, paragraph=True)
        return " ".join([r[1] for r in results]) if results else ""
    except Exception as e:
        print(f"[ERROR] OCR gagal untuk {img_path}: {e}")
        return ""


def get_page_from_filename(name: str):
    m = re.search(r'page[_\-]?(\d+)', name, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def clean_record(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_nasabah_records(full_text: str):
    """
    Pecah teks halaman jadi record per nasabah
    berdasarkan nomor kredit/SBG (15–16 digit angka).
    """
    pattern = r"(\d{15,16}.*?)(?=\s\d{15,16}|\Z)"
    matches = re.findall(pattern, full_text, flags=re.DOTALL)
    if matches:
        return [clean_record(m) for m in matches]
    return [clean_record(full_text)]


# === Ekstraksi Field ===
def extract_no_sbg(rec: str):
    m = re.search(r"\b\d{15,16}\b", rec)
    return m.group(0) if m else ""


def normalize_number(num_str: str) -> int:
    if not num_str:
        return 0
    clean = re.sub(r"[^\d]", "", num_str)
    if not clean:
        return 0
    val = int(clean)
    # koreksi angka janggal
    while val > 999_999_999:
        val //= 10
    while 0 < val < 100_000:
        val *= 10
    return val


def extract_fields_from_record(rec: str):
    """
    Dari satu record nasabah (jatuh_tempo):
    - no_sbg
    - taksiran (angka ke-3 dari belakang)
    - uang_pinjaman (angka ke-2 dari belakang)
    - sm (angka terakhir)
    """
    no_sbg = extract_no_sbg(rec)
    angka = re.findall(r"\d[\d.,]*", rec)

    taksiran, uang_pinjaman, sm = 0, 0, 0
    if len(angka) >= 3:
        taksiran = normalize_number(angka[-3])
        uang_pinjaman = normalize_number(angka[-2])
        sm = normalize_number(angka[-1])
    elif len(angka) == 2:
        uang_pinjaman = normalize_number(angka[-2])
        sm = normalize_number(angka[-1])
    elif len(angka) == 1:
        sm = normalize_number(angka[-1])

    return no_sbg, taksiran, uang_pinjaman, sm


# === Kredit Bermasalah khusus: ekstrak nama nasabah ===
def extract_nasabah_kb(rec: str, reader=None, img_path=None, bbox=None) -> str:
    """
    Ambil nama nasabah di record kredit bermasalah.
    Step:
    1. Regex utama: setelah CIF (6–12 digit) sebelum tanggal.
    2. Fallback regex: blok huruf kapital.
    3. Fallback terakhir: OCR ulang crop kolom Nasabah (jika bbox & img_path tersedia).
    """
    rec = str(rec)

    # regex pattern: NO_KREDIT + CIF + (NAMA) + TGL
    m = re.search(r"\d{15,16}\s+\d{6,12}\s+(.*?)(?=\s+\d{2}-\d{2}-\d{4})", rec)
    if m:
        nama = m.group(1).strip()
        if nama and not re.match(r"^\d{2}-\d{2}-\d{4}$", nama):
            return re.sub(r"\s+", " ", nama)

    # fallback regex: cari blok huruf kapital
    tokens = re.findall(r"[A-Z][A-Z\s\.,\-']{2,}", rec)
    if tokens:
        return tokens[0].strip()

    # fallback terakhir: OCR crop kolom Nasabah
    if reader and img_path and bbox:
        img = cv2.imread(img_path)
        x1, y1, x2, y2 = bbox
        crop = img[y1:y2, x1:x2]

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        result = reader.readtext(thresh, detail=0, paragraph=True)
        if result:
            return " ".join(result).strip()

    return "UNKNOWN_NASABAH"


# === Kredit Bermasalah (summary pinjaman/SM) ===
def extract_uang_pinjaman_sm_from_summary(full_text):
    """
    Cari baris 'Uang Pinjaman SM' (khusus kredit bermasalah).
    Return list pinjaman & sm.
    """
    m = re.search(r'Uang Pinjaman SM(.*)', full_text, re.IGNORECASE)
    if not m:
        return [], []
    angka = re.findall(r'\d[\d.,]*', m.group(1))
    uang_pinjaman_list = [normalize_number(a) for a in angka[::2]]
    sm_list = [normalize_number(a) for a in angka[1::2]]
    return uang_pinjaman_list, sm_list


# === Proses Dokumen ===
def process_doc_type(reader, doc_type: str):
    input_dir = os.path.join(IMAGES_DIR, doc_type)
    if not os.path.isdir(input_dir):
        print(f"[WARN] Folder tidak ditemukan: {input_dir}")
        return None, None

    files = sorted([
        f for f in os.listdir(input_dir) 
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ])
    if not files:
        print(f"[WARN] Tidak ada file gambar di {input_dir}")
        return None, None

    rows = []
    print(f"[INFO] Mulai proses {doc_type} ({len(files)} file)...")
    for fname in tqdm(files, desc=f"OCR {doc_type}", unit="file"):
        fpath = os.path.join(input_dir, fname)
        full_text = extract_text(reader, fpath)

        if not full_text.strip():
            rows.append({
                "filename": fname,
                "no": 0,
                "raw_text": "",
                "no_sbg": "",
                "taksiran": 0,
                "uang_pinjaman": 0,
                "sm": 0,
                "nasabah": "" if doc_type == "kredit_bermasalah" else None
            })
            continue

        records = split_nasabah_records(full_text)

        if doc_type == "jatuh_tempo":
            # khusus jatuh tempo → ambil angka per record
            for i, rec in enumerate(records, start=1):
                no_sbg, taksiran, uang_pinjaman, sm = extract_fields_from_record(rec)
                rows.append({
                    "filename": fname,
                    "no": i,
                    "raw_text": rec,
                    "no_sbg": no_sbg,
                    "taksiran": taksiran,
                    "uang_pinjaman": uang_pinjaman,
                    "sm": sm
                })
        else:
            # kredit bermasalah
            uang_pinjaman_list, sm_list = extract_uang_pinjaman_sm_from_summary(full_text)
            for i, rec in enumerate(records, start=1):
                no_sbg = extract_no_sbg(rec)

                # bbox bisa kamu set manual sesuai posisi kolom "Nasabah"
                nasabah = extract_nasabah_kb(rec, reader=reader, img_path=fpath, bbox=None)

                # log kalau nama hilang
                if nasabah == "UNKNOWN_NASABAH":
                    with open(MISSING_NAMES_LOG, "a", encoding="utf-8-sig") as f:
                        f.write(f"{fname},{i},{rec}\n")

                uang_pinjaman = uang_pinjaman_list[i-1] if i-1 < len(uang_pinjaman_list) else 0
                sm = sm_list[i-1] if i-1 < len(sm_list) else 0
                rows.append({
                    "filename": fname,
                    "no": i,
                    "raw_text": rec,
                    "no_sbg": no_sbg,
                    "nasabah": nasabah,
                    "taksiran": 0,
                    "uang_pinjaman": uang_pinjaman,
                    "sm": sm
                })

    df = pd.DataFrame(rows)
    stamp = dt.datetime.now().strftime("%Y%m%d")
    out_path = os.path.join(OUTPUT_DIR, f"{doc_type}_raw_{stamp}.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[INFO] Hasil {doc_type} disimpan: {out_path}")
    return df, out_path


def main():
    reader = get_reader()
    for doc_type in ("jatuh_tempo", "kredit_bermasalah"):
        process_doc_type(reader, doc_type)

def run_ocr_with_progress(image_files, output_dir, doc_type):
    """
    OCR dengan progress bar.
    - image_files: list path gambar hasil preprocessing
    - output_dir: folder output CSV
    - doc_type: 'jatuh_tempo' atau 'kredit_bermasalah'
    """
    if not image_files:
        print(f"[WARN] Tidak ada gambar untuk diproses di {doc_type}")
        return None, None

    reader = get_reader()
    rows = []

    print(f"[INFO] Mulai OCR {doc_type} ({len(image_files)} file)...")
    for img_path in tqdm(image_files, desc=f"OCR {doc_type}", unit="file"):
        full_text = extract_text(reader, img_path)

        if not full_text.strip():
            rows.append({
                "filename": os.path.basename(img_path),
                "no": 0,
                "raw_text": "",
                "no_sbg": "",
                "taksiran": 0,
                "uang_pinjaman": 0,
                "sm": 0,
                "nasabah": "" if doc_type == "kredit_bermasalah" else None
            })
            continue

        records = split_nasabah_records(full_text)

        if doc_type == "jatuh_tempo":
            for i, rec in enumerate(records, start=1):
                no_sbg, taksiran, uang_pinjaman, sm = extract_fields_from_record(rec)
                rows.append({
                    "filename": os.path.basename(img_path),
                    "no": i,
                    "raw_text": rec,
                    "no_sbg": no_sbg,
                    "taksiran": taksiran,
                    "uang_pinjaman": uang_pinjaman,
                    "sm": sm
                })
        else:
            uang_pinjaman_list, sm_list = extract_uang_pinjaman_sm_from_summary(full_text)
            for i, rec in enumerate(records, start=1):
                no_sbg = extract_no_sbg(rec)
                nasabah = extract_nasabah_kb(rec, reader=reader, img_path=img_path, bbox=None)

                if nasabah == "UNKNOWN_NASABAH":
                    with open(MISSING_NAMES_LOG, "a", encoding="utf-8-sig") as f:
                        f.write(f"{os.path.basename(img_path)},{i},{rec}\n")

                uang_pinjaman = uang_pinjaman_list[i-1] if i-1 < len(uang_pinjaman_list) else 0
                sm = sm_list[i-1] if i-1 < len(sm_list) else 0
                rows.append({
                    "filename": os.path.basename(img_path),
                    "no": i,
                    "raw_text": rec,
                    "no_sbg": no_sbg,
                    "nasabah": nasabah,
                    "taksiran": 0,
                    "uang_pinjaman": uang_pinjaman,
                    "sm": sm
                })

    # simpan hasil OCR ke dalam folder raw_ocr
    df = pd.DataFrame(rows)
    stamp = dt.datetime.now().strftime("%Y%m%d")

    raw_ocr_dir = os.path.join(output_dir, "raw_ocr")
    os.makedirs(raw_ocr_dir, exist_ok=True)

    out_path = os.path.join(raw_ocr_dir, f"{doc_type}_raw_{stamp}.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[INFO] Hasil OCR {doc_type} disimpan: {out_path}")
    return df, out_path

if __name__ == "__main__":
    main()
