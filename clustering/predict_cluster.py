import os
import pandas as pd
import joblib

def predict_clustering(input_path, model_path, scaler_path, output_dir):
    """
    Prediksi cluster dengan model KMeans yang sudah dilatih:
    - Input: preprocessed.csv
    - Load model: kmeans_model.pkl + scaler.pkl
    - Output: clustered_data.csv
    """
    # Load data
    df = pd.read_csv(input_path)

    if "UANG_PINJAMAN" not in df.columns:
        raise ValueError("Kolom 'UANG_PINJAMAN' tidak ada! Pastikan preprocessing sudah jalan.")

    # Load model & scaler
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model {model_path} tidak ditemukan. Jalankan training dulu.")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler {scaler_path} tidak ditemukan. Jalankan training dulu.")

    kmeans = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # Transform ulang pakai scaler
    df["PINJAMAN_SCALED"] = scaler.transform(df[["UANG_PINJAMAN"]])

    # Prediksi cluster
    df["CLUSTER"] = kmeans.predict(df[["PINJAMAN_SCALED"]])

    # Simpan hasil prediksi
    os.makedirs(output_dir, exist_ok=True)
    clustered_path = os.path.join(output_dir, "clustered_data.csv")
    df.to_csv(clustered_path, index=False)

    print("✅ Prediksi clustering selesai")
    print(f"📂 Data hasil clustering: {clustered_path}")

    # Distribusi cluster
    print("\n📊 Distribusi Cluster:")
    print(df["CLUSTER"].value_counts().sort_index())

    return clustered_path


if __name__ == "__main__":
  base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
  input_path = os.path.join(base_dir, "output", "clustering", "preprocessing", "preprocessed.csv")
  scaler_path = os.path.join(base_dir, "output", "clustering", "model", "scaler.pkl")
  model_path = os.path.join(base_dir, "output", "clustering", "model", "kmeans_model.pkl")
  output_dir = os.path.join(base_dir, "output", "clustering", "model")

  predict_clustering(input_path, model_path, scaler_path, output_dir)
