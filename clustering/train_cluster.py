import os
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib

def run_clustering(input_path, output_dir, n_clusters=3, random_state=42):
    # Load data
    df = pd.read_csv(input_path)

    # Pastikan kolom PINJAMAN_SCALED ada
    if "PINJAMAN_SCALED" not in df.columns:
        raise ValueError("Kolom PINJAMAN_SCALED tidak ditemukan! Jalankan preprocessing dulu.")

    # === Load scaler dari preprocessing biar konsisten ===
    scaler_path = os.path.join(os.path.dirname(input_path), "scaler.pkl")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError("Scaler dari preprocessing tidak ditemukan!")
    scaler = joblib.load(scaler_path)

    # Clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df["CLUSTER"] = kmeans.fit_predict(df[["PINJAMAN_SCALED"]])

    # Pastikan folder output ada
    os.makedirs(output_dir, exist_ok=True)

    # Simpan clustered dataset
    clustered_path = os.path.join(output_dir, "clustered_data.csv")
    df.to_csv(clustered_path, index=False)

    # Simpan model KMeans
    model_path = os.path.join(output_dir, "kmeans_model.pkl")
    joblib.dump(kmeans, model_path)

    print(f"✅ Clustering selesai.")
    print(f"📂 Data dengan cluster disimpan di: {clustered_path}")
    print(f"📦 Model disimpan di: {model_path}")
    print(f"📦 Scaler dipakai dari: {scaler_path}")

    return clustered_path, model_path, scaler_path


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "output", "clustering", "preprocessing", "preprocessed.csv")
    output_dir = os.path.join(base_dir, "output", "clustering", "model")
    run_clustering(input_path, output_dir, n_clusters=3)
