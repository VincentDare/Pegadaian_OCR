import os
import cv2
import numpy as np
from pdf2image import convert_from_path

# Folder dataset & output
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # root project
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
RAW_OCR_DIR = os.path.join(OUTPUT_DIR, "raw_ocr")

# Buat folder yang dibutuhkan
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(RAW_OCR_DIR, exist_ok=True)

# Deteksi apakah ada POPPLER_PATH (untuk Windows lokal)
if os.name == "nt":  # Windows
    POPPLER_PATH = r"C:\Users\Vincentdare\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"
else:
    POPPLER_PATH = None  # Linux/Mac → pakai poppler dari packages.txt

def get_table_rows(img):
    """
    Deteksi garis horizontal tabel untuk dapatkan koordinat baris (y).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Cari garis horizontal
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

    # Cari kontur garis
    contours, _ = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rows = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        rows.append(y)

    rows = sorted(rows)
    return rows

def remove_rubrik_column(img):
    """
    Hapus kolom Rubrik dari tabel (posisi tetap antara No. SBG dan Nasabah).
    """
    h, w = img.shape[:2]
    x1 = int(w * 0.16)
    x2 = int(w * 0.21)
    img[:, x1:x2] = 255
    return img


def remove_barang_jaminan_column(img):
    """
    Hapus kolom Barang Jaminan dari tabel (posisi tetap sebelum Taksiran).
    """
    h, w = img.shape[:2]
    x1 = int(w * 0.51)
    x2 = int(w * 0.73)
    img[:, x1:x2] = 255
    return img


def remove_alamat_nasabah(img):
    h, w = img.shape[:2]
    x1 = int(w * 0.21)
    x2 = int(w * 0.33)

    rows = get_table_rows(img)
    for i in range(len(rows)-1):
        y1, y2 = rows[i], rows[i+1]
        mid = (y1 + y2) // 2
        img[mid:y2, x1:x2] = 255

    return img

def remove_total_footer(img):
    """
    Hapus baris footer TOTAL di bagian bawah tabel.
    Berdasarkan gambar: TOTAL ada di ~92-100% dari tinggi gambar.
    """
    h, w = img.shape[:2]
    
    # Footer TOTAL biasanya di 92% ke bawah
    y1 = int(h * 0.92)
    y2 = h
    
    # Putihkan seluruh area footer (horizontal strip)
    img[y1:y2, :] = 255
    
    return img

def remove_header_tabel(img):
    """
    Hapus header judul kolom tabel:
    (No | No SBG | Nasabah | Telp/HP | Taksiran | Uang Pinjaman | SM)
    Disesuaikan dengan posisi nyata di file RPT_rptDaftarJatuhTempo_1754717274128_page1.png.
    """
    h, w = img.shape[:2]

    # Area header tabel (sekitar garis biru di contoh)
    # Jika resolusi gambar berbeda, sesuaikan proporsinya.
    y_start = int(h * 0.20)   # mulai di bawah tulisan "Cabang : UPC WANEA"
    y_end   = int(h * 0.26)   # berakhir tepat sebelum baris pertama data

    # Bersihkan area header (isi dengan putih)
    img[y_start:y_end, 0:w] = 255

    return img

def preprocess_image(img, output_path, mode="normal", keep_aspect_ratio=True,
                     remove_rubrik=True, remove_barang=True, remove_alamat=True):
    """
    Preprocessing gambar agar lebih jelas untuk OCR.
    """
    # Step 1: hapus kolom tertentu
    if remove_rubrik:
        img = remove_rubrik_column(img)
    if remove_barang:
        img = remove_barang_jaminan_column(img)
    if remove_alamat and mode == "jatuh_tempo":
        img = remove_header_tabel(img)              # hapus header
        img = remove_alamat_nasabah(img) 
        img = remove_total_footer(img)               # hapus footer TOTAL  

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize
    if keep_aspect_ratio:
        h, w = gray.shape
        scale = 1654 / w if w > 1654 else 1.0
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        resized = cv2.resize(gray, (1654, 2339))

    # Thresholding
    if mode == "jatuh_tempo":
        resized = cv2.resize(resized, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        thresh = cv2.adaptiveThreshold(
            resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 35, 11
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    else:
        _, cleaned = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cv2.imwrite(output_path, cleaned)


def pdf_to_images(pdf_path, output_folder, prefix="file", mode="normal", keep_aspect_ratio=True):
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)

    for i, page in enumerate(pages):
        page_path = os.path.join(output_folder, f"{prefix}_page{i+1}.png")
        page.save(page_path, "PNG")

        img = cv2.imread(page_path)
        preprocess_image(img, page_path, mode=mode, keep_aspect_ratio=keep_aspect_ratio)

    print(f"[INFO] {pdf_path} berhasil dikonversi ke {len(pages)} gambar (mode={mode}).")


def process_all_pdfs(keep_aspect_ratio=True):
    folder_mapping = {
        "Dataset Daftar Kredit Bermasalah": ("kredit_bermasalah",),
        "Dataset Daftar Kredit Jatuh Tempo": ("jatuh_tempo",),
    }

    for folder_name, (mode,) in folder_mapping.items():
        input_dir = os.path.join(DATASET_DIR, folder_name)
        output_dir = os.path.join(IMAGES_DIR, mode)
        os.makedirs(output_dir, exist_ok=True)

        for pdf_file in os.listdir(input_dir):
            if pdf_file.endswith(".pdf"):
                pdf_path = os.path.join(input_dir, pdf_file)
                prefix = os.path.splitext(pdf_file)[0]
                pdf_to_images(pdf_path, output_dir, prefix,
                              mode=mode, keep_aspect_ratio=keep_aspect_ratio)


def run_preprocessing(pdf_path, doc_type, base_output_dir, keep_aspect_ratio=True):
    output_dir = os.path.join(base_output_dir, "images", doc_type)
    os.makedirs(output_dir, exist_ok=True)

    prefix = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_to_images(pdf_path, output_dir, prefix, mode=doc_type, keep_aspect_ratio=keep_aspect_ratio)

    files = [
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.startswith(prefix) and f.endswith(".png")
    ]
    return files


if __name__ == "__main__":
    process_all_pdfs(keep_aspect_ratio=True)
