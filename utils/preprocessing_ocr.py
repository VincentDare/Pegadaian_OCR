import os
import cv2
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



def preprocess_image(img, output_path, mode="normal", keep_aspect_ratio=True):
    """
    Preprocessing gambar agar lebih jelas untuk OCR.
    mode:
      - kredit_bermasalah : simpan RAW tanpa preprocessing
      - jatuh_tempo       : fokus angka besar (adaptive threshold + resize)
    """
    if mode == "kredit_bermasalah":
        # Simpan apa adanya
        cv2.imwrite(output_path, img)
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if keep_aspect_ratio:
        h, w = gray.shape
        scale = 1654 / w if w > 1654 else 1.0
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        resized = cv2.resize(gray, (1654, 2339))  # paksa A4

    if mode == "jatuh_tempo":
        # Fokus angka → perbesar + adaptive threshold
        resized = cv2.resize(resized, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        thresh = cv2.adaptiveThreshold(
            resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 35, 11
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    else:
        # fallback normal otsu
        _, cleaned = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cv2.imwrite(output_path, cleaned)


def pdf_to_images(pdf_path, output_folder, prefix="file", mode="normal", keep_aspect_ratio=True):
    """
    Konversi PDF ke image per halaman dan lakukan preprocessing.
    """
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)

    for i, page in enumerate(pages):
        page_path = os.path.join(output_folder, f"{prefix}_page{i+1}.png")
        page.save(page_path, "PNG")

        img = cv2.imread(page_path)
        preprocess_image(img, page_path, mode=mode, keep_aspect_ratio=keep_aspect_ratio)

    print(f"[INFO] {pdf_path} berhasil dikonversi ke {len(pages)} gambar (mode={mode}).")


def process_all_pdfs(keep_aspect_ratio=True):
    """
    Loop semua PDF dalam dataset sesuai struktur folder kamu.
    Mode otomatis sesuai nama folder.
    """
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

    # Hanya ambil file gambar untuk PDF ini (prefix cocok)
    files = [
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.startswith(prefix) and f.endswith(".png")
    ]
    return files


if __name__ == "__main__":
    process_all_pdfs(keep_aspect_ratio=True)
