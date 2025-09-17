import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis
import numpy as np 

def run_eda(input_path, output_dir):
    """
    Exploratory Data Analysis (EDA) untuk UANG_PINJAMAN.
    - Statistik deskriptif (mean, median, std, skewness, kurtosis)
    - Histogram + KDE (normal & log-scale)
    - Boxplot
    """
    # Load data
    df = pd.read_csv(input_path)

    # Pastikan kolom ada
    if "UANG_PINJAMAN" not in df.columns:
        raise ValueError("Kolom 'UANG_PINJAMAN' tidak ditemukan di dataset!")

    # Drop NA
    uang = df["UANG_PINJAMAN"].dropna()

    # === Statistik Deskriptif ===
    desc = uang.describe()
    stats = {
        "mean": uang.mean(),
        "median": uang.median(),
        "std": uang.std(),
        "skewness": skew(uang),
        "kurtosis": kurtosis(uang)
    }

    print("\n📊 Statistik Deskriptif:")
    print(desc)
    print(stats)

    # Pastikan folder output ada
    os.makedirs(output_dir, exist_ok=True)

    # Simpan summary
    desc.to_csv(os.path.join(output_dir, "eda_describe.csv"))
    pd.DataFrame([stats]).to_csv(os.path.join(output_dir, "eda_summary.csv"), index=False)

    print(f"✅ Summary EDA disimpan di {output_dir}")

    # === Histogram + KDE ===
    plt.figure(figsize=(8, 5))
    sns.histplot(uang, kde=True, bins=30)
    plt.title("Distribusi UANG_PINJAMAN")
    plt.xlabel("UANG_PINJAMAN (Rp)")
    plt.ylabel("Frekuensi")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "histogram.png"))
    plt.close()

    # Log-scale histogram
    plt.figure(figsize=(8, 5))
    sns.histplot(uang[uang > 0].apply(lambda x: np.log10(x)), kde=True, bins=30, color="orange")
    plt.title("Distribusi Log(UANG_PINJAMAN)")
    plt.xlabel("Log10(UANG_PINJAMAN)")
    plt.ylabel("Frekuensi")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "histogram_log.png"))
    plt.close()

    # === Boxplot ===
    plt.figure(figsize=(6, 4))
    sns.boxplot(x=uang)
    plt.title("Boxplot UANG_PINJAMAN")
    plt.xlabel("UANG_PINJAMAN (Rp)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "boxplot.png"))
    plt.close()

    print(f"✅ Grafik disimpan di {output_dir}")


if __name__ == "__main__":
    # Ambil root project
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # naik 1 level dari clustering
    input_path = os.path.join(base_dir, "output", "clustering", "preprocessing", "preprocessed.csv")
    output_dir = os.path.join(base_dir, "output", "clustering", "eda")


    run_eda(input_path, output_dir)
