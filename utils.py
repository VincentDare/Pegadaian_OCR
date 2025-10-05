import os
import shutil
from config import DATASET_DIR, OUTPUT_DIR

def hapus_file(path: str):
    if os.path.exists(path):
        os.remove(path)

def hapus_folder(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)

def hapus_semua_data():
    hapus_folder(DATASET_DIR)
    hapus_folder(OUTPUT_DIR)
    os.makedirs(DATASET_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
