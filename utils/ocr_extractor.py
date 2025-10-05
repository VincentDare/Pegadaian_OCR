import os
import re
import datetime as dt
import pandas as pd
import easyocr
from tqdm import tqdm
import cv2

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

# === OCR helpers ===
def extract_text(reader, img_path: str) -> str:
    """Paragraph=True untuk flow lama (kredit_bermasalah)"""
    try:
        results = reader.readtext(img_path, detail=1, paragraph=True)
        return " ".join([r[1] for r in results]) if results else ""
    except Exception as e:
        print(f"[ERROR] OCR gagal untuk {img_path}: {e}")
        return ""

def extract_text_boxes(reader, img_path: str):
    """Paragraph=False untuk ambil box-by-box (jatuh_tempo)"""
    try:
        return reader.readtext(img_path, detail=1, paragraph=False)
    except Exception as e:
        print(f"[ERROR] OCR (boxes) gagal untuk {img_path}: {e}")
        return []

def clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def get_page_from_filename(name: str):
    m = re.search(r'page[_\-]?(\d+)', name, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None

# === General helpers ===
def extract_no_sbg(text: str) -> str:
    m = re.search(r"\b(\d{15,16})\b", text)
    return m.group(1) if m else ""

def _normalize_int_simple(val: str) -> int:
    if not val:
        return 0
    clean = re.sub(r"[^\d]", "", val)
    return int(clean) if clean else 0

def normalize_number(num_str: str) -> int:
    """Versi robust untuk angka berformat dengan titik/koma - TANPA koreksi otomatis"""
    if not num_str:
        return 0
    clean = re.sub(r"[^\d]", "", num_str)
    if not clean:
        return 0
    return int(clean)

def _group_lines_by_y(ocr_results, y_tol=25):
    """
    Group hasil OCR per-baris tabel berdasarkan posisi Y.
    ocr_results: list of (bbox, text, prob)
    """
    if not ocr_results:
        return []

    items = []
    for bbox, text, prob in ocr_results:
        # bbox is list of 4 points: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        ys = [p[1] for p in bbox]
        y_top = min(ys)
        xs = [p[0] for p in bbox]
        x_left = min(xs)
        items.append((y_top, x_left, text))

    items.sort(key=lambda t: (t[0], t[1]))

    lines = []
    current = []
    last_y = None
    for y, x, text in items:
        if last_y is None or abs(y - last_y) < y_tol:
            current.append((x, text))
            last_y = y
        else:
            current.sort(key=lambda t: t[0])
            line_text = " ".join(t for _, t in current)
            lines.append(clean_whitespace(line_text))
            current = [(x, text)]
            last_y = y

    if current:
        current.sort(key=lambda t: t[0])
        line_text = " ".join(t for _, t in current)
        lines.append(clean_whitespace(line_text))

    return [ln for ln in lines if ln]

# === NEW: Extraction functions for jatuh_tempo ONLY ===
def extract_nasabah_jt(raw_text: str) -> str:
    """
    Ekstrak nama nasabah untuk jatuh_tempo:
    - Mulai setelah No_SBG (15-16 digit)
    - Berhenti SEBELUM nomor telepon (08xxx) ATAU tanggal (DD-MM-YYYY) ATAU angka koma
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    parse_text = raw_text
    parse_text = re.sub(r"\s+", " ", parse_text).strip()
    parse_text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", parse_text)
    parse_text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", parse_text)
    parse_text = re.sub(r"[^0-9A-Za-z\s\.,\-:\/]", " ", parse_text)
    parse_text = re.sub(r"\s+", " ", parse_text).strip()

    # Cari No_SBG
    m = re.search(r"\b(\d{15,16})\b", parse_text)
    if not m:
        return ""

    start = m.end()
    tail = parse_text[start:].strip()
    if not tail:
        return ""

    # Cari pembatas: nomor telepon, tanggal, atau angka dengan koma
    # Priority: telepon > tanggal > angka koma
    telp_match = re.search(r"(08\d{8,11})", tail)
    date_match = re.search(r"\b\d{2}-\d{2}-\d{4}\b", tail)
    num_match = re.search(r"\d{1,3}[.,]\d{3}", tail)
    
    # Ambil pembatas pertama yang ditemukan
    cutoff = len(tail)
    if telp_match:
        cutoff = min(cutoff, telp_match.start())
    if date_match:
        cutoff = min(cutoff, date_match.start())
    if num_match:
        cutoff = min(cutoff, num_match.start())
    
    nama_raw = tail[:cutoff].strip()
    
    # Bersihkan tanda baca di awal/akhir
    nama_raw = re.sub(r"^[\W_]+|[\W_]+$", "", nama_raw)
    return nama_raw.strip()

def extract_telp_jt(raw_text: str) -> str:
    """
    Ekstrak nomor telepon (08xxx dengan panjang 10-13 digit).
    Jika ada lebih dari 1, gabung dengan semicolon.
    """
    if not raw_text:
        return ""
    
    # Hilangkan word boundary agar bisa deteksi nomor yang nempel
    telps = re.findall(r"08\d{8,11}", raw_text)
    telps = [t for t in telps if 10 <= len(t) <= 13]
    return "; ".join(sorted(set(telps)))

def extract_tanggal_jt(raw_text: str) -> tuple:
    """
    Ekstrak tanggal (format DD-MM-YYYY).
    Return tuple: (tgl_kredit, tgl_jatuh_tempo)
    """
    if not raw_text:
        return ("", "")
    
    tgls = re.findall(r"\b\d{2}-\d{2}-\d{4}\b", raw_text)
    tgl_kredit = tgls[0] if len(tgls) > 0 else ""
    tgl_jt = tgls[1] if len(tgls) > 1 else ""
    return (tgl_kredit, tgl_jt)

def extract_financial_triple_jt(parse_text: str) -> tuple:
    """
    Ekstrak tiga angka terakhir: (taksiran, uang_pinjaman, sm).
    Filter:
    - Buang No_SBG (16 digit)
    - Buang nomor telepon (range 8-9 billion, covers 08xxxxxxxxx patterns)
    - Buang tahun (4 digit: 2024, 2025, dll)
    - Buang angka TOTAL yang spesifik (901392824, 781774200, 66871800)
    - Ambil angka financial valid
    """
    # CRITICAL: Buang baris TOTAL jika OCR ikut baca
    parse_text = re.sub(r'TOTAL.*', '', parse_text, flags=re.IGNORECASE)
    
    # Known TOTAL values yang harus dibuang (dari page 9)
    TOTAL_VALUES = {901392824, 781774200, 66871800}
    
    # Temukan semua angka dengan format ribuan atau plain digit
    all_nums = re.findall(r"\d{1,3}(?:[.,]\d{3})+|\d{3,}", parse_text)
    
    # Filter dan bersihkan
    cleaned_nums = []
    for n in all_nums:
        val = normalize_number(n)
        original_len = len(n.replace(",", "").replace(".", ""))
        
        # Filter rules:
        # 1. Buang No_SBG (16 digit)
        if original_len == 16:
            continue
        
        # 2. Buang tahun (exactly 4 digit: 2024, 2025, etc)
        if original_len == 4:
            continue
        
        # 3. Buang nomor telepon yang masuk sebagai angka
        # Nomor HP Indonesia normalized: 800 juta - 900 miliar (0.8B - 900B)
        # Ini covers: 08xxxxxxxx (10 digit) sampai 08xxxxxxxxxxx (13 digit)
        if 800_000_000 <= val <= 900_000_000_000:
            continue
        
        # 4. CRITICAL: Buang angka TOTAL yang specific
        if val in TOTAL_VALUES:
            continue
        
        # 5. Ambil angka valid (>= 100 untuk cover SM kecil, < 1B max)
        if val >= 100 and val < 1_000_000_000:
            cleaned_nums.append(val)
    
    # Ambil 3 angka terakhir
    if len(cleaned_nums) >= 3:
        return (cleaned_nums[-3], cleaned_nums[-2], cleaned_nums[-1])
    elif len(cleaned_nums) == 2:
        return (cleaned_nums[-2], cleaned_nums[-1], 0)
    elif len(cleaned_nums) == 1:
        return (0, 0, cleaned_nums[-1])
    return (0, 0, 0)

# === (TIDAK DIUBAH) Kredit bermasalah functions ===
def is_valid_record(rec: str) -> bool:
    """
    Cek apakah record nasabah valid.
    - Harus punya No_SBG (15–16 digit)
    - DAN minimal punya nama (huruf kapital panjang) atau tanggal
    """
    if not re.search(r"\b\d{15,16}\b", rec):
        return False
    if re.search(r"\d{2}-\d{2}-\d{4}", rec):
        return True
    if re.search(r"[A-Z]{3,}(?:\s+[A-Z]{2,})*", rec):
        return True
    return False

def split_nasabah_records(full_text: str):
    pattern = r"(\d{15,16}.*?)(?=\s\d{15,16}|\Z)"
    matches = re.findall(pattern, full_text, flags=re.DOTALL)
    records = []
    for m in matches:
        rec = clean_whitespace(m)
        if is_valid_record(rec):
            records.append(rec)
    return records

def extract_fields_from_record(rec: str):
    """
    Versi lama (digunakan oleh kredit_bermasalah flow),
    dipertahankan agar tidak mengganggu proses kredit_bermasalah.
    """
    no_sbg = extract_no_sbg(rec)
    nasabah = ""
    nasabah_match = re.findall(r"KT\s+([A-Z][A-Z\s]+)", rec)
    if nasabah_match:
        nasabah = nasabah_match[-1].strip()
        nasabah = re.sub(r"\b(LINGKUNGAN|RT|RW|KEL|JAGA)\b.*", "", nasabah).strip()

    telps = re.findall(r"0[82]\d[\d\s\-]{7,15}", rec)
    telps = [re.sub(r"\D", "", t) for t in telps]
    telps = [t for t in telps if 10 <= len(t) <= 13]
    telp_hp = "; ".join(sorted(set(telps)))

    tgls = re.findall(r"\d{2}-\d{2}-\d{4}", rec)
    tgl_kredit = tgls[0] if len(tgls) > 0 else ""
    tgl_jt = tgls[1] if len(tgls) > 1 else ""

    barang_jaminan = ""
    barang_match = re.search(r"(SATU|DUA|TIGA|EMPAT).*?(?:GRAM|EMAS)", rec)
    if barang_match:
        barang_jaminan = barang_match.group(0).strip()

    angka = re.findall(r"\d{1,3}(?:[.,]\d{3})+", rec)
    vals = [int(a.replace(".", "").replace(",", "")) for a in angka]
    vals = sorted(vals, reverse=True)

    taksiran, uang_pinjaman, sm = (vals + [0, 0, 0])[:3]
    return {
        "no_sbg": no_sbg,
        "nasabah": nasabah,
        "telp_hp": telp_hp,
        "tgl_kredit": tgl_kredit,
        "tgl_jatuh_tempo": tgl_jt,
        "barang_jaminan": barang_jaminan,
        "taksiran": taksiran,
        "uang_pinjaman": uang_pinjaman,
        "sm": sm
    }

def extract_nasabah_kb(rec: str, reader=None, img_path=None, bbox=None) -> str:
    """
    Dipertahankan tanpa ubahan (kredit_bermasalah).
    """
    rec = str(rec)
    m = re.search(r"\d{15,16}\s+\d{6,12}\s+(.*?)(?=\s+\d{2}-\d{2}-\d{4})", rec)
    if m:
        nama = m.group(1).strip()
        if nama and not re.match(r"^\d{2}-\d{2}-\d{4}$", nama):
            return re.sub(r"\s+", " ", nama)
    tokens = re.findall(r"[A-Z][A-Z\s\.,\-']{2,}", rec)
    if tokens:
        return tokens[0].strip()
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

def extract_uang_pinjaman_sm_from_summary(full_text):
    m = re.search(r'Uang Pinjaman SM(.*)', full_text, re.IGNORECASE)
    if not m:
        return [], []
    angka = re.findall(r'\d[\d.,]*', m.group(1))
    uang_pinjaman_list = [normalize_number(a) for a in angka[::2]]
    sm_list = [normalize_number(a) for a in angka[1::2]]
    return uang_pinjaman_list, sm_list

# === Process only for jatuh_tempo (plus kredit_bermasalah left intact) ===
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

        if doc_type == "jatuh_tempo":
            # NEW flow: Ambil semua teks di page, lalu split per No_SBG record
            full_text = extract_text(reader, fpath)
            
            if not full_text.strip():
                continue
            
            # CRITICAL: Remove TOTAL footer line before processing
            # Strategy: Cut everything after last valid No_SBG record
            # Find all No_SBG positions
            sbg_matches = list(re.finditer(r'\b\d{15,16}\b', full_text))
            if sbg_matches:
                # Find the last No_SBG position
                last_sbg_end = sbg_matches[-1].end()
                # Find where this record likely ends (before "TOTAL" or "Di" signature)
                tail_text = full_text[last_sbg_end:]
                
                # Find cutoff point (TOTAL, signature markers, or end of meaningful data)
                cutoff_match = re.search(r'\b(TOTAL|Di\s+anggal|Dibuat\s+Oleh)', tail_text, re.IGNORECASE)
                
                if cutoff_match:
                    # Keep only up to the last record (before TOTAL/signature)
                    full_text = full_text[:last_sbg_end + cutoff_match.start()]
                else:
                    # No explicit cutoff found, look for pattern of last record ending
                    # Typically: No_SBG + name + phones + dates + 3 numbers
                    # Try to find where numbers stop being part of individual records
                    lines = tail_text.split('\n')
                    valid_lines = []
                    for line in lines:
                        # Stop if line looks like footer/total
                        if re.search(r'(TOTAL|^\s*\d{3},\d{3},\d{3}\s*$)', line, re.IGNORECASE):
                            break
                        valid_lines.append(line)
                    full_text = full_text[:last_sbg_end] + '\n'.join(valid_lines)
            
            # Preprocessing: fix OCR errors dan separate concatenated names
            parse_text = full_text
            parse_text = re.sub(r"\s+", " ", parse_text)
            parse_text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", parse_text)
            parse_text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", parse_text)
            # Fix OCR errors
            parse_text = re.sub(r"\bBTANS\b", "STANS", parse_text)
            parse_text = re.sub(r"\bBTEVEN\b", "STEVEN", parse_text)
            parse_text = re.sub(r"ELIZABETHHOTMA", "ELIZABETH HOTMA", parse_text)
            # Separate concatenated names
            parse_text = re.sub(r"(AYU)(?=NAD)", r"\1 ", parse_text)
            parse_text = re.sub(r"(ROOSYE)(?=REWAH)", r"\1 ", parse_text)
            parse_text = re.sub(r"(YERFIN)(?=LAGANDESA)", r"\1 ", parse_text)
            parse_text = re.sub(r"(JUNITA)(?=KELLY)", r"\1 ", parse_text)
            parse_text = re.sub(r"(HERLY)(?=SANGGRA)", r"\1 ", parse_text)
            parse_text = re.sub(r"(ROONA)(?=INRI)", r"\1 ", parse_text)
            parse_text = re.sub(r"(INRI)(?=DEVI)", r"\1 ", parse_text)
            parse_text = re.sub(r"(DEVI)(?=LASUT)", r"\1 ", parse_text)
            parse_text = re.sub(r"(TEO)(?=WAILAN)", r"\1 ", parse_text)
            parse_text = re.sub(r"(VYCENCY)(?=TACYA)", r"\1 ", parse_text)
            parse_text = re.sub(r"(ROSMIA)(?=KUBA)", r"ROSMI ", parse_text)
            # Fix OCR errors in numbers (letter 'o' as zero at end)
            parse_text = re.sub(r"(\d+,\d+)\s*[oO]+\b", r"\1", parse_text)  # Fix "1,202,0oo" -> "1,202"
            parse_text = re.sub(r"[^0-9A-Za-z\s\.,\-:\/]", " ", parse_text)
            parse_text = re.sub(r"\s+", " ", parse_text).strip()
            
            # NEW STRATEGY: Split records individually dengan boundary yang lebih ketat
            # Find all No_SBG positions first
            sbg_positions = [(m.group(1), m.start(), m.end()) for m in re.finditer(r'(\d{15,16})', parse_text)]
            
            if not sbg_positions:
                continue
            
            no_counter = 1
            for idx, (no_sbg, start_pos, end_pos) in enumerate(sbg_positions):
                # Determine where this record ends
                if idx + 1 < len(sbg_positions):
                    # Record ends just before next No_SBG
                    next_start = sbg_positions[idx + 1][1]
                    rec = parse_text[start_pos:next_start]
                else:
                    # Last record - be very careful here!
                    # Strategy: Keep everything UNTIL we hit TOTAL keyword or signature
                    tail = parse_text[start_pos:]
                    
                    # Look for TOTAL keyword or signature markers
                    cutoff_patterns = [
                        r'\bTOTAL\b',
                        r'Di\s+anggal',
                        r'Dibuat\s+Oleh',
                        r'KOTA\s+MANADO'
                    ]
                    
                    cutoff_pos = None
                    for pattern in cutoff_patterns:
                        match = re.search(pattern, tail, re.IGNORECASE)
                        if match:
                            if cutoff_pos is None or match.start() < cutoff_pos:
                                cutoff_pos = match.start()
                    
                    if cutoff_pos:
                        rec = tail[:cutoff_pos]
                    else:
                        rec = tail
                
                rec = clean_whitespace(rec)
                
                # Skip if record is too short or looks like footer
                if len(rec) < 20 or re.search(r'\bTOTAL\b', rec, re.IGNORECASE):
                    continue
                
                # Verify No_SBG matches
                extracted_sbg = extract_no_sbg(rec)
                if extracted_sbg != no_sbg:
                    continue
                
                # Extract fields
                nasabah = extract_nasabah_jt(rec)
                telp_hp = extract_telp_jt(rec)
                tgl_kredit, tgl_jt = extract_tanggal_jt(rec)
                taksiran, uang_pinjaman, sm = extract_financial_triple_jt(rec)

                rows.append({
                    "filename": fname,
                    "No": no_counter,
                    "No_SBG": no_sbg,
                    "Nasabah": nasabah,
                    "Telp_HP": telp_hp,
                    "Tgl_Kredit": tgl_kredit,
                    "Tgl_Jatuh_Tempo": tgl_jt,
                    "Taksiran": taksiran,
                    "Uang_Pinjaman": uang_pinjaman,
                    "SM": sm
                })
                no_counter += 1

        else:
            # KREDIT BERMASALAH: flow lama dipertahankan (tidak diutak-atik)
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
            uang_pinjaman_list, sm_list = extract_uang_pinjaman_sm_from_summary(full_text)
            for i, rec in enumerate(records, start=1):
                no_sbg = extract_no_sbg(rec)
                nasabah = extract_nasabah_kb(rec, reader=reader, img_path=fpath, bbox=None)

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

    # Export hasil OCR
    df = pd.DataFrame(rows)
    stamp = dt.datetime.now().strftime("%Y%m%d")
    out_path = os.path.join(OUTPUT_DIR, f"{doc_type}_raw_{stamp}.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[INFO] Hasil {doc_type} disimpan: {out_path}")
    return df, out_path

def main():
    reader = get_reader()
    # Proses jatuh_tempo dan kredit_bermasalah seperti semula (keduanya ada)
    for doc_type in ("jatuh_tempo", "kredit_bermasalah"):
        process_doc_type(reader, doc_type)

if __name__ == "__main__":
    main()