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
    - Analisis temporal (jika ada TGL_JATUH_TEMPO)
    """
    # Load data
    df = pd.read_csv(input_path)

    print(f"[INFO] Kolom tersedia: {df.columns.tolist()}")
    print(f"[INFO] Total record: {len(df)}")

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

    print("\n=== Statistik Deskriptif UANG_PINJAMAN ===")
    print(desc)
    print("\n=== Statistik Tambahan ===")
    for key, val in stats.items():
        print(f"{key}: {val:,.2f}")

    # Pastikan folder output ada
    os.makedirs(output_dir, exist_ok=True)

    # Simpan summary
    desc.to_csv(os.path.join(output_dir, "eda_describe.csv"))
    pd.DataFrame([stats]).to_csv(os.path.join(output_dir, "eda_summary.csv"), index=False)

    print(f"\n[OK] Summary EDA disimpan di {output_dir}")

    # === Visualisasi ===
    # 1. Histogram + KDE
    plt.figure(figsize=(10, 6))
    sns.histplot(uang, kde=True, bins=30, color='steelblue')
    plt.title("Distribusi UANG_PINJAMAN", fontsize=14, fontweight='bold')
    plt.xlabel("UANG_PINJAMAN (Rp)", fontsize=12)
    plt.ylabel("Frekuensi", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "histogram.png"), dpi=300)
    plt.close()

    # 2. Log-scale histogram
    plt.figure(figsize=(10, 6))
    log_uang = uang[uang > 0].apply(lambda x: np.log10(x))
    sns.histplot(log_uang, kde=True, bins=30, color="orange")
    plt.title("Distribusi Log10(UANG_PINJAMAN)", fontsize=14, fontweight='bold')
    plt.xlabel("Log10(UANG_PINJAMAN)", fontsize=12)
    plt.ylabel("Frekuensi", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "histogram_log.png"), dpi=300)
    plt.close()

    # 3. Boxplot
    plt.figure(figsize=(10, 4))
    sns.boxplot(x=uang, color='lightcoral')
    plt.title("Boxplot UANG_PINJAMAN", fontsize=14, fontweight='bold')
    plt.xlabel("UANG_PINJAMAN (Rp)", fontsize=12)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "boxplot.png"), dpi=300)
    plt.close()

    # === Analisis Temporal (jika ada TGL_JATUH_TEMPO) ===
    if "TGL_JATUH_TEMPO" in df.columns:
        print("\n[INFO] Melakukan analisis temporal berdasarkan TGL_JATUH_TEMPO")
        
        # Convert tanggal
        df['TGL_PARSED'] = pd.to_datetime(df['TGL_JATUH_TEMPO'], format='%d-%m-%Y', errors='coerce')
        df_temporal = df.dropna(subset=['TGL_PARSED', 'UANG_PINJAMAN'])
        
        if len(df_temporal) > 0:
            # Groupby by month
            df_temporal['BULAN'] = df_temporal['TGL_PARSED'].dt.to_period('M')
            monthly_stats = df_temporal.groupby('BULAN').agg({
                'UANG_PINJAMAN': ['sum', 'mean', 'count']
            }).reset_index()
            
            monthly_stats.columns = ['BULAN', 'TOTAL_PINJAMAN', 'RATA_RATA_PINJAMAN', 'JUMLAH_NASABAH']
            monthly_stats['BULAN'] = monthly_stats['BULAN'].astype(str)
            
            # Simpan statistik temporal
            monthly_stats.to_csv(os.path.join(output_dir, "eda_temporal_monthly.csv"), index=False)
            
            # Plot timeline
            plt.figure(figsize=(12, 6))
            plt.subplot(2, 1, 1)
            plt.bar(monthly_stats['BULAN'], monthly_stats['TOTAL_PINJAMAN'], color='steelblue')
            plt.title("Total UANG_PINJAMAN per Bulan", fontsize=12, fontweight='bold')
            plt.ylabel("Total (Rp)", fontsize=10)
            plt.xticks(rotation=45)
            plt.grid(axis='y', alpha=0.3)
            
            plt.subplot(2, 1, 2)
            plt.bar(monthly_stats['BULAN'], monthly_stats['JUMLAH_NASABAH'], color='orange')
            plt.title("Jumlah Nasabah per Bulan", fontsize=12, fontweight='bold')
            plt.ylabel("Jumlah Nasabah", fontsize=10)
            plt.xticks(rotation=45)
            plt.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "temporal_analysis.png"), dpi=300)
            plt.close()
            
            print(f"[OK] Analisis temporal disimpan")
    
    print(f"\n[OK] Semua grafik disimpan di {output_dir}")
    return desc, stats


if __name__ == "__main__":
    # Ambil root project
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_path = os.path.join(base_dir, "output", "clustering", "preprocessing", "preprocessed.csv")
    output_dir = os.path.join(base_dir, "output", "clustering", "eda")

    run_eda(input_path, output_dir)