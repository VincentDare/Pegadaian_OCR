import os
import pandas as pd
from sklearn.cluster import KMeans
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

def run_clustering(input_path, output_dir, n_clusters=3, random_state=42):
    """
    Training model KMeans clustering:
    - Input: preprocessed.csv (harus ada PINJAMAN_SCALED)
    - Output: clustered_data.csv + kmeans_model.pkl
    - Visualisasi: cluster distribution & scatter plot
    """
    # Load data
    df = pd.read_csv(input_path)

    print(f"[INFO] Kolom tersedia: {df.columns.tolist()}")
    print(f"[INFO] Total record: {len(df)}")

    # Pastikan kolom PINJAMAN_SCALED ada
    if "PINJAMAN_SCALED" not in df.columns:
        raise ValueError("Kolom PINJAMAN_SCALED tidak ditemukan! Jalankan preprocessing dulu.")

    # === Load scaler dari preprocessing biar konsisten ===
    model_dir = os.path.dirname(output_dir)
    scaler_path = os.path.join(model_dir, "model", "scaler.pkl")
    
    # Coba cari di preprocessing folder jika tidak ada di model folder
    if not os.path.exists(scaler_path):
        scaler_path = os.path.join(os.path.dirname(input_path), "..", "model", "scaler.pkl")
    
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(
            f"Scaler dari preprocessing tidak ditemukan!\n"
            f"Jalankan preprocessing terlebih dahulu."
        )
    
    scaler = joblib.load(scaler_path)
    print(f"[OK] Scaler loaded dari: {scaler_path}")

    # === Clustering ===
    print(f"[INFO] Memulai clustering dengan {n_clusters} cluster...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df["CLUSTER"] = kmeans.fit_predict(df[["PINJAMAN_SCALED"]])

    # Pastikan folder output ada
    os.makedirs(output_dir, exist_ok=True)

    # === Analisis Cluster ===
    print("\n=== Analisis Hasil Clustering ===")
    cluster_summary = df.groupby("CLUSTER").agg({
        "UANG_PINJAMAN": ["count", "mean", "min", "max", "std"]
    }).round(2)
    cluster_summary.columns = ["Jumlah", "Rata-rata", "Min", "Max", "Std"]
    print(cluster_summary)

    # Simpan cluster summary
    cluster_summary.to_csv(os.path.join(output_dir, "cluster_summary.csv"))

    # === Simpan clustered dataset ===
    clustered_path = os.path.join(output_dir, "clustered_data.csv")
    df.to_csv(clustered_path, index=False, encoding="utf-8-sig")

    # === Simpan model KMeans ===
    model_path = os.path.join(output_dir, "kmeans_model.pkl")
    joblib.dump(kmeans, model_path)

    # === Visualisasi ===
    # 1. Distribusi cluster
    plt.figure(figsize=(10, 6))
    cluster_counts = df["CLUSTER"].value_counts().sort_index()
    plt.bar(cluster_counts.index, cluster_counts.values, color='steelblue')
    plt.title("Distribusi Cluster", fontsize=14, fontweight='bold')
    plt.xlabel("Cluster", fontsize=12)
    plt.ylabel("Jumlah Nasabah", fontsize=12)
    plt.xticks(cluster_counts.index)
    plt.grid(axis='y', alpha=0.3)
    
    # Tambahkan label jumlah di atas bar
    for i, v in enumerate(cluster_counts.values):
        plt.text(i, v + max(cluster_counts.values)*0.01, str(v), 
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "cluster_distribution.png"), dpi=300)
    plt.close()

    # 2. Scatter plot (UANG_PINJAMAN vs CLUSTER)
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
    plt.title("Scatter Plot: UANG_PINJAMAN per Cluster", fontsize=14, fontweight='bold')
    plt.xlabel("Index Data", fontsize=12)
    plt.ylabel("UANG_PINJAMAN (Rp)", fontsize=12)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "cluster_scatter.png"), dpi=300)
    plt.close()

    # 3. Boxplot per cluster
    plt.figure(figsize=(10, 6))
    df_plot = df[["CLUSTER", "UANG_PINJAMAN"]].copy()
    df_plot["CLUSTER"] = df_plot["CLUSTER"].astype(str)
    sns.boxplot(data=df_plot, x="CLUSTER", y="UANG_PINJAMAN", palette="Set2")
    plt.title("Boxplot UANG_PINJAMAN per Cluster", fontsize=14, fontweight='bold')
    plt.xlabel("Cluster", fontsize=12)
    plt.ylabel("UANG_PINJAMAN (Rp)", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "cluster_boxplot.png"), dpi=300)
    plt.close()

    print(f"\n[OK] Clustering selesai!")
    print(f"📂 Data dengan cluster: {clustered_path}")
    print(f"📦 Model KMeans: {model_path}")
    print(f"📊 Cluster summary: {os.path.join(output_dir, 'cluster_summary.csv')}")
    print(f"📈 Visualisasi tersimpan di: {output_dir}")

    return clustered_path, model_path, scaler_path


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "output", "clustering", "preprocessing", "preprocessed.csv")
    output_dir = os.path.join(base_dir, "output", "clustering", "model")
    run_clustering(input_path, output_dir, n_clusters=3)