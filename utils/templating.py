import json
import pandas as pd
from datetime import datetime
import os
import urllib.parse

TEMPLATE_FILE = os.path.join("config", "templates.json")

def load_templates():
    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        return json.load(f)

def generate_messages(df: pd.DataFrame, doc_type: str, template_override=None):
    templates = load_templates()
    template = template_override if template_override else templates.get(doc_type, "")

    messages = []
    for _, row in df.iterrows():
        msg = template
        for col in df.columns:
            msg = msg.replace(f"{{{col}}}", str(row.get(col, "")))
        messages.append(msg.strip())
    return messages

def build_whatsapp_links(df: pd.DataFrame, messages):
    """Tambahkan kolom WhatsApp App dan Web link berdasarkan TELP_HP (jika ada)."""
    wa_app, wa_web = [], []
    for i, row in df.iterrows():
        telp = str(row.get("TELP_HP", "")).strip()
        msg = urllib.parse.quote(messages[i])  # encode pesan
        if telp and telp.isdigit():
            wa_app.append(f"https://wa.me/{telp}?text={msg}")
            wa_web.append(f"https://web.whatsapp.com/send?phone={telp}&text={msg}")
        else:
            wa_app.append("")
            wa_web.append("")
    return wa_app, wa_web

def save_messages(messages, doc_type, df=None):
    date_str = datetime.now().strftime("%Y%m%d")
    out_dir = "output/messages"
    os.makedirs(out_dir, exist_ok=True)

    if df is not None:
        df_out = df.copy()
        df_out["Pesan"] = messages

        # tambah link WA
        wa_app, wa_web = build_whatsapp_links(df_out, messages)
        df_out["WhatsApp_App"] = wa_app
        df_out["WhatsApp_Web"] = wa_web

        csv_file = os.path.join(out_dir, f"{doc_type}_messages_{date_str}.csv")
        df_out.to_csv(csv_file, index=False, encoding="utf-8-sig")
        print(f"[INFO] Pesan {doc_type} disimpan → {csv_file}")
        return csv_file

    return None

def run_templating(df: pd.DataFrame, doc_type: str):
    """Generate pesan + simpan ke CSV untuk pipeline"""
    messages = generate_messages(df, doc_type)
    return save_messages(messages, doc_type, df)


if __name__ == "__main__":
    print("[INFO] Modul templating siap dipakai di pipeline.")

