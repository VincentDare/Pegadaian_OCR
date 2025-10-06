# evaluate.py
import os
import pandas as pd
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def run_evaluation(input_path, output_dir):
    """
    Evaluasi hasil clustering dengan internal metrics:
    - Silhouette Score (0 to 1, semakin tinggi semakin baik)
    - Calinski-Harabasz Index (semakin tinggi semakin baik)
    - Davies-Bouldin Index (semakin rendah semakin baik)
    - Visualisasi silhouette analysis per cluster
    - Interpretasi hasil untuk business context PT Pegadaian
    """
    # Load dataset hasil clustering
    df = pd.read_csv(input_path)

    print(f"[INFO] Kolom tersedia: {df.columns.tolist()}")
    print(f"[INFO] Total record: {len(df)}")

    # Pastikan folder output ada
    os.makedirs(output_dir, exist_ok=True)

    # Ambil fitur yang diskalakan untuk perhitungan metrics
    X = df[["PINJAMAN_SCALED"]].values
    labels = df["CLUSTER"].values

    # === Internal Metrics ===
    sil_score = silhouette_score(X, labels)
    ch_score = calinski_harabasz_score(X, labels)
    db_score = davies_bouldin_score(X, labels)

    metrics = {
        "Silhouette Score": sil_score,
        "Calinski-Harabasz Index": ch_score,
        "Davies-Bouldin Index": db_score,
        "Number of Clusters": len(df["CLUSTER"].unique()),
        "Total Data Points": len(df)
    }

    # === Interpretasi Metrics ===
    interpretation = []
    
    # Silhouette Score interpretation
    if sil_score >= 0.7:
        sil_interp = "Sangat Baik - Cluster sangat terpisah dan compact"
    elif sil_score >= 0.5:
        sil_interp = "Baik - Cluster cukup terpisah"
    elif sil_score >= 0.25:
        sil_interp = "Cukup - Ada overlap antar cluster"
    else:
        sil_interp = "Kurang Baik - Cluster overlap signifikan"
    
    interpretation.append(f"Silhouette Score ({sil_score:.4f}): {sil_interp}")
    
    # Davies-Bouldin Index interpretation
    if db_score < 0.5:
        db_interp = "Sangat Baik - Cluster sangat terpisah"
    elif db_score < 1.0:
        db_interp = "Baik - Cluster cukup terpisah"
    else:
        db_interp = "Perlu Perbaikan - Cluster overlap"
    
    interpretation.append(f"Davies-Bouldin Index ({db_score:.4f}): {db_interp}")
    
    # Calinski-Harabasz interpretation (relatif, semakin tinggi semakin baik)
    interpretation.append(f"Calinski-Harabasz Index ({ch_score:.2f}): Semakin tinggi semakin baik (nilai relatif)")

    # Simpan metrics ke CSV
    metrics_path = os.path.join(output_dir, "evaluation_metrics.csv")
    pd.DataFrame([metrics]).to_csv(metrics_path, index=False)

    # Simpan interpretasi
    interp_path = os.path.join(output_dir, "evaluation_interpretation.txt")
    with open(interp_path, "w", encoding="utf-8") as f:
        f.write("=== Evaluasi Clustering PT Pegadaian ===\n\n")
        f.write("Metrics:\n")
        for k, v in metrics.items():
            if isinstance(v, float):
                f.write(f"- {k}: {v:.4f}\n")
            else:
                f.write(f"- {k}: {v}\n")
        f.write("\nInterpretasi:\n")
        for line in interpretation:
            f.write(f"- {line}\n")
        f.write("\nRekomendasi Bisnis:\n")
        f.write("- Gunakan cluster untuk segmentasi strategi penagihan\n")
        f.write("- Cluster dengan pinjaman besar perlu monitoring lebih ketat\n")
        f.write("- Cluster dengan pinjaman kecil bisa menggunakan automated reminder\n")

    print("\n=== Internal Metrics ===")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"- {k}: {v:.4f}")
        else:
            print(f"- {k}: {v}")

    print("\n=== Interpretasi ===")
    for line in interpretation:
        print(f"- {line}")

    # === Visualisasi Silhouette Analysis ===
    from sklearn.metrics import silhouette_samples

    silhouette_vals = silhouette_samples(X, labels)
    df['silhouette'] = silhouette_vals

    # Plot silhouette per cluster
    n_clusters = len(df["CLUSTER"].unique())
    fig, ax = plt.subplots(figsize=(10, 6))

    y_lower = 10
    for i in sorted(df["CLUSTER"].unique()):
        cluster_silhouette_vals = silhouette_vals[labels == i]
        cluster_silhouette_vals.sort()

        size_cluster_i = cluster_silhouette_vals.shape[0]
        y_upper = y_lower + size_cluster_i

        color = plt.cm.viridis(float(i) / n_clusters)
        ax.fill_betweenx(np.arange(y_lower, y_upper),
                         0, cluster_silhouette_vals,
                         facecolor=color, edgecolor=color, alpha=0.7)

        ax.text(-0.05, y_lower + 0.5 * size_cluster_i, f'Cluster {i}')
        y_lower = y_upper + 10

    ax.set_title("Silhouette Analysis per Cluster", fontsize=14, fontweight='bold')
    ax.set_xlabel("Silhouette Coefficient", fontsize=12)
    ax.set_ylabel("Cluster", fontsize=12)
    ax.axvline(x=sil_score, color="red", linestyle="--", label=f"Avg Score: {sil_score:.3f}")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "silhouette_analysis.png"), dpi=300)
    plt.close()

    # === Visualisasi Perbandingan Metrics ===
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Silhouette Score
    axes[0].bar(['Silhouette\nScore'], [sil_score], color='steelblue')
    axes[0].set_ylim(0, 1)
    axes[0].set_title('Silhouette Score\n(Higher is Better)', fontweight='bold')
    axes[0].axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Good threshold')
    axes[0].text(0, sil_score + 0.05, f'{sil_score:.3f}', ha='center', fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)
    axes[0].legend()

    # Davies-Bouldin Index
    axes[1].bar(['Davies-Bouldin\nIndex'], [db_score], color='coral')
    axes[1].set_title('Davies-Bouldin Index\n(Lower is Better)', fontweight='bold')
    axes[1].axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Good threshold')
    axes[1].text(0, db_score + 0.05, f'{db_score:.3f}', ha='center', fontweight='bold')
    axes[1].grid(axis='y', alpha=0.3)
    axes[1].legend()

    # Calinski-Harabasz Index
    axes[2].bar(['Calinski-Harabasz\nIndex'], [ch_score], color='lightgreen')
    axes[2].set_title('Calinski-Harabasz Index\n(Higher is Better)', fontweight='bold')
    axes[2].text(0, ch_score + ch_score*0.05, f'{ch_score:.1f}', ha='center', fontweight='bold')
    axes[2].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "metrics_comparison.png"), dpi=300)
    plt.close()

    # === Distribusi Silhouette per Cluster ===
    plt.figure(figsize=(10, 6))
    cluster_labels = [f"Cluster {i}" for i in sorted(df["CLUSTER"].unique())]
    silhouette_by_cluster = [df[df["CLUSTER"] == i]["silhouette"].values 
                             for i in sorted(df["CLUSTER"].unique())]
    
    bp = plt.boxplot(silhouette_by_cluster, labels=cluster_labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], plt.cm.viridis(np.linspace(0, 1, n_clusters))):
        patch.set_facecolor(color)
    
    plt.axhline(y=sil_score, color='red', linestyle='--', label=f'Avg: {sil_score:.3f}')
    plt.title("Distribusi Silhouette Score per Cluster", fontsize=14, fontweight='bold')
    plt.ylabel("Silhouette Coefficient", fontsize=12)
    plt.xlabel("Cluster", fontsize=12)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "silhouette_boxplot.png"), dpi=300)
    plt.close()

    print(f"\n[OK] Metrics disimpan di {metrics_path}")
    print(f"[OK] Interpretasi disimpan di {interp_path}")
    print(f"[OK] Visualisasi tersimpan di {output_dir}")

    return metrics


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_path = os.path.join(base_dir, "output", "clustering", "model", "predicted_clusters.csv")
    output_dir = os.path.join(base_dir, "output", "clustering", "evaluation")

    run_evaluation(input_path, output_dir)