# evaluate.py
import os
import pandas as pd
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

def run_evaluation(input_path, output_dir):
    """
    Evaluasi hasil clustering dengan internal metrics:
    - Silhouette Score
    - Calinski-Harabasz Index
    - Davies-Bouldin Index
    """
    # Load dataset hasil clustering
    df = pd.read_csv(input_path)

    # Pastikan folder output ada
    os.makedirs(output_dir, exist_ok=True)

    # Ambil fitur yang diskalakan untuk perhitungan metrics
    X = df[["PINJAMAN_SCALED"]]
    labels = df["CLUSTER"]

    # === Internal Metrics ===
    sil_score = silhouette_score(X, labels)
    ch_score = calinski_harabasz_score(X, labels)
    db_score = davies_bouldin_score(X, labels)

    metrics = {
        "Silhouette Score": sil_score,
        "Calinski-Harabasz Index": ch_score,
        "Davies-Bouldin Index": db_score
    }

    # Simpan metrics ke CSV
    metrics_path = os.path.join(output_dir, "evaluation_metrics.csv")
    pd.DataFrame([metrics]).to_csv(metrics_path, index=False)

    print("\n📊 Internal Metrics:")
    for k, v in metrics.items():
        print(f"- {k}: {v:.4f}")
    print(f"✅ Metrics disimpan di {metrics_path}")


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # naik 1 level dari clustering
    input_path = os.path.join(base_dir, "output", "clustering", "model", "clustered_data.csv")
    output_dir = os.path.join(base_dir, "output", "clustering", "evaluation")

    run_evaluation(input_path, output_dir)
