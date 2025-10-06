import os
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

def predict_clustering(input_path, model_path, scaler_path, output_dir):
    """
    Prediksi cluster dengan model KMeans yang sudah dilatih:
    - Input: preprocessed.csv (data baru yang sudah di-preprocessing)
    - Load model: kmeans_model.pkl + scaler.pkl
    - Output: clustered_data.csv dengan kolom CLUSTER
    - Visualisasi: distribusi cluster hasil prediksi
    """
    # Load data
    df = pd.read_csv(input_path)

    print(f"[INFO] Kolom tersedia: {df.columns.tolist()}")
    print(f"[INFO] Total record: {len(df)}")

    if "UANG_PINJAMAN" not in df.columns:
        raise ValueError("Kolom 'UANG_PINJAMAN' tidak ada! Pastikan preprocessing sudah jalan.")

    # Load model & scaler
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model {model_path} tidak ditemukan.\n"
            f"Jalankan training terlebih dahulu dengan train_model.py"
        )
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(
            f"Scaler {scaler_path} tidak ditemukan.\n"
            f"Jalankan preprocessing terlebih dahulu."
        )

    kmeans = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    print(f"[OK] Model loaded: {model_path}")
    print(f"[OK] Scaler loaded: {scaler_path}")

    # Transform ulang pakai scaler (jika belum ada PINJAMAN_SCALED)
    if "PINJAMAN_SCALED" not in df.columns:
        df["PINJAMAN_SCALED"] = scaler.transform(df[["UANG_PINJAMAN"]])
        print("[INFO] Melakukan scaling pada UANG_PINJAMAN")

    # Prediksi cluster
    print(f"[INFO] Melakukan prediksi cluster...")
    df["CLUSTER"] = kmeans.predict(df[["PINJAMAN_SCALED"]])

    # === Analisis Hasil Prediksi ===
    print("\n=== Hasil Prediksi Clustering ===")
    cluster_summary = df.groupby("CLUSTER").agg({
        "UANG_PINJAMAN": ["count", "mean", "min", "max", "std"]
    }).round(2)
    cluster_summary.columns = ["Jumlah", "Rata-rata", "Min", "Max", "Std"]
    print(cluster_summary)

    # Distribusi cluster
    print("\n=== Distribusi Cluster ===")
    print(df["CLUSTER"].value_counts().sort_index())

    # Simpan hasil prediksi
    os.makedirs(output_dir, exist_ok=True)
    clustered_path = os.path.join(output_dir, "predicted_clusters.csv")
    df.to_csv(clustered_path, index=False, encoding="utf-8-sig")

    # Simpan cluster summary
    cluster_summary.to_csv(os.path.join(output_dir, "predicted_cluster_summary.csv"))

    # === Visualisasi ===
    # 1. Distribusi cluster
    plt.figure(figsize=(10, 6))
    cluster_counts = df["CLUSTER"].value_counts().sort_index()
    plt.bar(cluster_counts.index, cluster_counts.values, color='coral')
    plt.title("Distribusi Cluster (Prediksi)", fontsize=14, fontweight='bold')
    plt.xlabel("Cluster", fontsize=12)
    plt.ylabel("Jumlah Nasabah", fontsize=12)
    plt.xticks(cluster_counts.index)
    plt.grid(axis='y', alpha=0.3)
    
    # Tambahkan label jumlah
    for i, v in enumerate(cluster_counts.values):
        plt.text(i, v + max(cluster_counts.values)*0.01, str(v), 
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "predicted_distribution.png"), dpi=300)
    plt.close()

    # 2. Boxplot per cluster
    plt.figure(figsize=(10, 6))
    df_plot = df[["CLUSTER", "UANG_PINJAMAN"]].copy()
    df_plot["CLUSTER"] = df_plot["CLUSTER"].astype(str)
    sns.boxplot(data=df_plot, x="CLUSTER", y="UANG_PINJAMAN", palette="Set3")
    plt.title("Boxplot UANG_PINJAMAN per Cluster (Prediksi)", fontsize=14, fontweight='bold')
    plt.xlabel("Cluster", fontsize=12)
    plt.ylabel("UANG_PINJAMAN (Rp)", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "predicted_boxplot.png"), dpi=300)
    plt.close()

    # 3. Scatter plot
    plt.figure(figsize=(12, 6))
    for cluster in sorted(df["CLUSTER"].unique()):
        cluster_data = df[df["CLUSTER"] == cluster]
        plt.scatter(
            cluster_data.index, 
            cluster_data["UANG_PINJAMAN"],
            label=f"Cluster {cluster}",
            alpha=0.6,
            s=50
        )
    plt.title("Scatter Plot: UANG_PINJAMAN per Cluster (Prediksi)", fontsize=14, fontweight='bold')
    plt.xlabel("Index Data", fontsize=12)
    plt.ylabel("UANG_PINJAMAN (Rp)", fontsize=12)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "predicted_scatter.png"), dpi=300)
    plt.close()

    print(f"\n[OK] Prediksi clustering selesai!")
    print(f"📂 Data hasil prediksi: {clustered_path}")
    print(f"📊 Cluster summary: {os.path.join(output_dir, 'predicted_cluster_summary.csv')}")
    print(f"📈 Visualisasi tersimpan di: {output_dir}")

    return clustered_path


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_path = os.path.join(base_dir, "output", "clustering", "preprocessing", "preprocessed.csv")
    scaler_path = os.path.join(base_dir, "output", "clustering", "model", "scaler.pkl")
    model_path = os.path.join(base_dir, "output", "clustering", "model", "kmeans_model.pkl")
    output_dir = os.path.join(base_dir, "output", "clustering", "predictions")

    predict_clustering(input_path, model_path, scaler_path, output_dir)