import json
import os

# Ambil folder root project (auto-extractor)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def load_json(filename):
    """
    General loader untuk membaca file JSON di folder /config/
    """
    path = os.path.join(BASE_DIR, "config", filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"[ERROR] File config tidak ditemukan: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"[ERROR] Format JSON invalid di {filename}: {e}")

def get_templates():
    """
    Load template pesan otomatis dari templates.json
    """
    return load_json("templates.json")

def get_fields():
    """
    Load struktur field dari struktur_fields.json
    """
    return load_json("struktur_fields.json")
