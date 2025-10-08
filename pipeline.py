import os
import sys
import time
import threading
from tqdm import tqdm

# Tambahkan path utils & clustering
sys.path.append("utils")
sys.path.append("clustering")

import utils.preprocessing_ocr as preprocessing_ocr
import utils.ocr_extractor as ocr_extractor
import utils.postprocessing as postprocessing
import utils.cleaning_std as cleaning_std
import utils.parsers as parsers

import clustering.dataset as dataset
import clustering.preprocessing as preprocessing
import clustering.eda as eda
import clustering.train_cluster as train_clustering
import clustering.predict_cluster as predict_clustering
import clustering.evaluate as evaluate
import clustering.visualize as visualize

BASE_DIR = os.path.dirname(__file__)
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# --- Cleanup otomatis ---
def schedule_cleanup(delay=1800):
    def _cleanup():
        print("\n🧹 Menjalankan cleanup otomatis...")
        # Hapus isi dataset
        for root, dirs, files in os.walk(DATASET_DIR):
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                except Exception as e:
                    print(f"[WARN] Gagal hapus {f}: {e}")

        # Hapus isi images
        for root, dirs, files in os.walk(IMAGES_DIR):
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                except Exception as e:
                    print(f"[WARN] Gagal hapus {f}: {e}")

        # Hapus isi output, kecuali model
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for f in files:
                if f not in ["kmeans_model.pkl", "scaler.pkl"]:
                    try:
                        os.remove(os.path.join(root, f))
                    except Exception as e:
                        print(f"[WARN] Gagal hapus {f}: {e}")

        print("✅ Cleanup otomatis selesai!")

    t = threading.Timer(delay, _cleanup)
    t.daemon = True
    t.start()


# --- Clustering helper ---
def clustering_step(input_path, model_dir):
    model_path = os.path.join(model_dir, "kmeans_model.pkl")
    scaler_path = os.path.join(model_dir, "scaler.pkl")

    if os.path.exists(model_path) and os.path.exists(scaler_path):
        print("✅ Model sudah ada → langsung Prediksi Clustering")
        predict_clustering.predict_clustering(input_path, model_path, scaler_path, model_dir)
    else:
        print("⚠️ Model belum ada → Training dulu")
        train_clustering.run_clustering(input_path, model_dir, n_clusters=3)


# --- OCR Helper untuk pipeline ---
def run_ocr_for_doc_type(doc_type: str):
    """
    Wrapper untuk menjalankan OCR extraction berdasarkan doc_type.
    Menggunakan fungsi process_doc_type dari ocr_extractor.
    """
    print(f"[INFO] Memulai OCR extraction untuk {doc_type}...")
    
    # Inisialisasi reader
    reader = ocr_extractor.get_reader()
    
    # Proses OCR
    df, out_path = ocr_extractor.process_doc_type(reader, doc_type)
    
    if df is not None:
        print(f"[INFO] OCR {doc_type} selesai: {len(df)} records extracted")
        return df, out_path
    else:
        print(f"[WARN] OCR {doc_type} tidak menghasilkan data")
        return None, None


# --- Pipeline per PDF ---
def run_pipeline_per_pdf(pdf_path: str, doc_type: str):
    print("\n==============================")
    print(f"🚀 Memproses PDF: {pdf_path} (type={doc_type})")

    # Step 0: Preprocessing PDF → Images
    print("\n📌 Step 0: Preprocessing PDF → Images")
    try:
        image_files = preprocessing_ocr.run_preprocessing(
            pdf_path,
            doc_type,
            base_output_dir=BASE_DIR,
            keep_aspect_ratio=True
        )
        print(f"[INFO] {len(image_files)} gambar berhasil dibuat untuk OCR")
    except Exception as e:
        print(f"[ERROR] Gagal preprocessing PDF: {e}")
        return

    # Steps pipeline utama
    steps = [
        ("OCR Extractor", lambda: run_ocr_for_doc_type(doc_type)),
        ("Postprocessing", lambda: postprocessing.run_postprocessing_wrapper(OUTPUT_DIR)),
        ("Cleaning", lambda: cleaning_std.run_cleaning(OUTPUT_DIR)),
        ("Parsing", lambda: parsers.parse_document(doc_type)),
        ("Dataset Merge", lambda: dataset.run_dataset()),
        ("Preprocessing", lambda: preprocessing.run_preprocessing()),
        ("EDA", lambda: eda.run_eda(
            os.path.join(OUTPUT_DIR, "clustering", "preprocessing", "preprocessed.csv"),
            os.path.join(OUTPUT_DIR, "clustering", "eda")
        )),
        ("Clustering", lambda: clustering_step(
            os.path.join(OUTPUT_DIR, "clustering", "preprocessing", "preprocessed.csv"),
            os.path.join(OUTPUT_DIR, "clustering", "model")
        )),
        ("Evaluation", lambda: evaluate.run_evaluation(
            os.path.join(OUTPUT_DIR, "clustering", "model", "clustered_data.csv"),
            os.path.join(OUTPUT_DIR, "clustering", "evaluation")
        )),
        ("Visualization & Summary", lambda: visualize.run_visualization(
            os.path.join(OUTPUT_DIR, "clustering", "model", "clustered_data.csv"),
            os.path.join(OUTPUT_DIR, "clustering", "visualization"),
            os.path.join(OUTPUT_DIR, "clustering", "summary")
        )),
    ]

    with tqdm(total=len(steps), desc=f"Pipeline Progress ({doc_type})", unit="step") as pbar:
        for step_name, func in steps:
            print(f"\n📌 Step: {step_name}")
            try:
                func()
            except Exception as e:
                print(f"[ERROR] Gagal di step {step_name}: {e}")
            pbar.update(1)
            time.sleep(0.1)

    print(f"\n✅ Selesai memproses PDF: {pdf_path}\n")


def run_pipeline_all(update_progress=None):
    folder_mapping = {
        "jatuh_tempo": "Dataset Daftar Kredit Jatuh Tempo",
        "kredit_bermasalah": "Dataset Daftar Kredit Bermasalah"
    }

    total_steps = 7  # Dataset merge → Preprocessing → EDA → Clustering → Eval → Visualisasi → Cleanup
    current = 0

    # --- Step 1: Preprocessing & OCR semua PDF per doc_type ---
    for doc_type, folder_name in folder_mapping.items():
        input_dir = os.path.join(DATASET_DIR, folder_name)
        
        if not os.path.exists(input_dir):
            print(f"[WARN] Folder tidak ditemukan: {input_dir}")
            continue
            
        pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]

        if not pdf_files:
            print(f"[INFO] Tidak ada PDF di folder {input_dir}")
            continue

        print(f"\n===== Preprocessing & OCR untuk: {doc_type} =====")
        
        # Preprocessing semua PDF menjadi images
        for pdf_file in pdf_files:
            pdf_path = os.path.join(input_dir, pdf_file)
            try:
                image_files = preprocessing_ocr.run_preprocessing(
                    pdf_path, doc_type, base_output_dir=BASE_DIR
                )
                print(f"[INFO] {len(image_files)} images dari {pdf_file}")
            except Exception as e:
                print(f"[ERROR] Gagal preprocessing {pdf_file}: {e}")

        # Jalankan OCR untuk semua images doc_type ini
        try:
            run_ocr_for_doc_type(doc_type)
        except Exception as e:
            print(f"[ERROR] Gagal OCR untuk {doc_type}: {e}")

        # Jalankan postprocessing, cleaning, parsing untuk doc_type ini
        try:
            postprocessing.run_postprocessing_wrapper(OUTPUT_DIR)
            cleaning_std.run_cleaning(OUTPUT_DIR)
            parsers.parse_document(doc_type)
        except Exception as e:
            print(f"[ERROR] Gagal post-processing untuk {doc_type}: {e}")

    # --- Step 2: Pipeline clustering ---
    steps = [
        ("Dataset Merge", lambda: dataset.run_dataset()),
        ("Preprocessing", lambda: preprocessing.run_preprocessing()),
        ("EDA", lambda: eda.run_eda(
            os.path.join(OUTPUT_DIR, "clustering", "preprocessing", "preprocessed.csv"),
            os.path.join(OUTPUT_DIR, "clustering", "eda")
        )),
        ("Clustering", lambda: clustering_step(
            os.path.join(OUTPUT_DIR, "clustering", "preprocessing", "preprocessed.csv"),
            os.path.join(OUTPUT_DIR, "clustering", "model")
        )),
        ("Evaluation", lambda: evaluate.run_evaluation(
            os.path.join(OUTPUT_DIR, "clustering", "model", "predicted_clusters.csv"),
            os.path.join(OUTPUT_DIR, "clustering", "evaluation")
        )),
        ("Visualization & Summary", lambda: visualize.run_visualization(
            os.path.join(OUTPUT_DIR, "clustering", "model", "predicted_clusters.csv"),
            os.path.join(OUTPUT_DIR, "clustering", "visualization"),
            os.path.join(OUTPUT_DIR, "clustering", "summary")
        )),
        ("Cleanup", lambda: schedule_cleanup(delay=1800)),
    ]

    for i, (name, func) in enumerate(steps, 1):
        print(f"\n📌 Step: {name}")
        try:
            func()
        except Exception as e:
            print(f"[ERROR] Gagal di step {name}: {e}")

        if update_progress:
            update_progress(int(i / total_steps * 100), f"{name} ✅")

    print("\n✅ Pipeline selesai untuk semua folder\n")


if __name__ == "__main__":
    run_pipeline_all()