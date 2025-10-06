# visualize.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import numpy as np

def run_visualization(input_path, output_dir_vis, output_dir_sum):
    """
    Visualisasi hasil clustering untuk PT Pegadaian:
    - Mapping cluster otomatis: Pinjaman Kecil → Menengah → Besar
    - Visualisasi standar: Bar chart, Boxplot, Histogram, Pie chart
    - Visualisasi temporal (jika ada TGL_JATUH_TEMPO):
      * Total pinjaman per tanggal
      * Distribusi nasabah per tanggal
      * Segmen pinjaman per tanggal
      * Tren akumulasi pinjaman
      * Top nasabah berisiko tinggi (jatuh tempo terdekat + nominal besar)
    """
    # Load data
    df = pd.read_csv(input_path)

    print(f"[INFO] Kolom tersedia: {df.columns.tolist()}")
    print(f"[INFO] Total record: {len(df)}")

    # === Tentukan urutan cluster otomatis (dari rata-rata kecil ke besar) ===
    cluster_order = (
        df.groupby("CLUSTER")["UANG_PINJAMAN"]
        .mean()
        .sort_values()
        .index.tolist()
    )

    # === Mapping cluster labels dinamis ===
    CLUSTER_LABELS = {}
    for i, cluster_id in enumerate(cluster_order, start=1):
        CLUSTER_LABELS[cluster_id] = f"Segmen {i}"

    # Mapping label cluster
    df["CLUSTER_LABEL"] = df["CLUSTER"].map(CLUSTER_LABELS)

    # Pastikan folder output ada
    os.makedirs(output_dir_vis, exist_ok=True)
    os.makedirs(output_dir_sum, exist_ok=True)

    # === Timestamp biar file tidak ketimpa ===
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Tentukan urutan label yang ada saja
    label_order = list(CLUSTER_LABELS.values())

    # ========================================
    # VISUALISASI STANDAR
    # ========================================

    # === 1. Barplot rata-rata pinjaman per cluster ===
    cluster_means = (
        df.groupby("CLUSTER_LABEL")["UANG_PINJAMAN"]
        .mean()
        .reindex(label_order)
    )
    plt.figure(figsize=(10, 6))
    sns.barplot(
        x=cluster_means.index,
        y=cluster_means.values,
        hue=cluster_means.index,
        legend=False,
        palette="viridis"
    )
    plt.title("Rata-rata Pinjaman per Segmen", fontsize=14, fontweight='bold')
    plt.xlabel("Segmen Nasabah", fontsize=12)
    plt.ylabel("Rata-rata Pinjaman (Rp)", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    for i, v in enumerate(cluster_means.values):
        plt.text(i, v, f"Rp {v:,.0f}", ha="center", va="bottom", fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_bar_{stamp}.png"), dpi=300)
    plt.close()

    # === 2. Barplot jumlah nasabah per cluster ===
    cluster_counts_abs = df["CLUSTER_LABEL"].value_counts().reindex(label_order)
    plt.figure(figsize=(10, 6))
    sns.barplot(
        x=cluster_counts_abs.index,
        y=cluster_counts_abs.values,
        hue=cluster_counts_abs.index,
        legend=False,
        palette="Blues"
    )
    plt.title("Jumlah Nasabah per Segmen", fontsize=14, fontweight='bold')
    plt.xlabel("Segmen Nasabah", fontsize=12)
    plt.ylabel("Jumlah Nasabah", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    for i, v in enumerate(cluster_counts_abs.values):
        plt.text(i, v, str(v), ha="center", va="bottom", fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_count_bar_{stamp}.png"), dpi=300)
    plt.close()

    # === 3. Boxplot distribusi pinjaman ===
    plt.figure(figsize=(10, 6))
    sns.boxplot(
        x="CLUSTER_LABEL",
        y="UANG_PINJAMAN",
        data=df,
        hue="CLUSTER_LABEL",
        order=label_order,
        legend=False,
        palette="Set2"
    )
    plt.title("Distribusi Pinjaman per Segmen (Boxplot)", fontsize=14, fontweight='bold')
    plt.xlabel("Segmen Nasabah", fontsize=12)
    plt.ylabel("Nilai Pinjaman (Rp)", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_boxplot_{stamp}.png"), dpi=300)
    plt.close()

    # === 4. Histogram distribusi pinjaman ===
    plt.figure(figsize=(12, 6))
    sns.histplot(
        data=df,
        x="UANG_PINJAMAN",
        hue="CLUSTER_LABEL",
        bins=30,
        kde=True,
        multiple="stack",
        hue_order=label_order
    )
    plt.title("Sebaran Pinjaman per Segmen (Histogram)", fontsize=14, fontweight='bold')
    plt.xlabel("Uang Pinjaman (Rp)", fontsize=12)
    plt.ylabel("Jumlah Nasabah", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_histogram_{stamp}.png"), dpi=300)
    plt.close()

    # === 5. Pie chart distribusi nasabah ===
    cluster_counts = (
        df["CLUSTER_LABEL"].value_counts(normalize=True)
        .reindex(label_order) * 100
    )
    plt.figure(figsize=(8, 8))
    plt.pie(
        cluster_counts,
        labels=cluster_counts.index,
        autopct="%.1f%%",
        colors=sns.color_palette("pastel"),
        startangle=90
    )
    plt.title("Distribusi Nasabah per Segmen", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_pie_{stamp}.png"), dpi=300)
    plt.close()

    # ========================================
    # VISUALISASI TEMPORAL (jika ada TGL_JATUH_TEMPO)
    # ========================================
    
    has_temporal = False
    if "TGL_JATUH_TEMPO" in df.columns:
        print("\n[INFO] Membuat visualisasi temporal berdasarkan TGL_JATUH_TEMPO")
        
        # Parse tanggal
        df['TGL_PARSED'] = pd.to_datetime(df['TGL_JATUH_TEMPO'], format='%d-%m-%Y', errors='coerce')
        df_temporal = df.dropna(subset=['TGL_PARSED']).copy()
        
        if len(df_temporal) > 0:
            has_temporal = True
            
            # Sort by date
            df_temporal = df_temporal.sort_values('TGL_PARSED')
            
            # === 6. Total Pinjaman per Tanggal (Bar Chart) ===
            daily_sum = df_temporal.groupby('TGL_PARSED')['UANG_PINJAMAN'].sum()
            
            plt.figure(figsize=(14, 6))
            plt.bar(daily_sum.index, daily_sum.values, color='steelblue', alpha=0.7)
            plt.title("Total Pinjaman per Tanggal Jatuh Tempo", fontsize=14, fontweight='bold')
            plt.xlabel("Tanggal Jatuh Tempo", fontsize=12)
            plt.ylabel("Total Pinjaman (Rp)", fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir_vis, f"temporal_total_pinjaman_{stamp}.png"), dpi=300)
            plt.close()
            
            # === 7. Distribusi Nasabah per Tanggal (Bar Chart) ===
            daily_count = df_temporal.groupby('TGL_PARSED').size()
            
            plt.figure(figsize=(14, 6))
            plt.bar(daily_count.index, daily_count.values, color='coral', alpha=0.7)
            plt.title("Jumlah Nasabah per Tanggal Jatuh Tempo", fontsize=14, fontweight='bold')
            plt.xlabel("Tanggal Jatuh Tempo", fontsize=12)
            plt.ylabel("Jumlah Nasabah", fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir_vis, f"temporal_jumlah_nasabah_{stamp}.png"), dpi=300)
            plt.close()
            
            # === 8. Segmen Pinjaman per Tanggal (Stacked Bar) ===
            segment_by_date = df_temporal.groupby(['TGL_PARSED', 'CLUSTER_LABEL'])['UANG_PINJAMAN'].sum().unstack(fill_value=0)
            
            plt.figure(figsize=(14, 6))
            segment_by_date.plot(kind='bar', stacked=True, colormap='viridis', ax=plt.gca())
            plt.title("Segmen Pinjaman per Tanggal Jatuh Tempo", fontsize=14, fontweight='bold')
            plt.xlabel("Tanggal Jatuh Tempo", fontsize=12)
            plt.ylabel("Total Pinjaman (Rp)", fontsize=12)
            plt.legend(title="Segmen", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir_vis, f"temporal_segment_stacked_{stamp}.png"), dpi=300)
            plt.close()
            
            # === 9. Tren Akumulasi Pinjaman ===
            df_temporal['AKUMULASI_PINJAMAN'] = df_temporal['UANG_PINJAMAN'].cumsum()
            
            plt.figure(figsize=(14, 6))
            plt.plot(df_temporal['TGL_PARSED'], df_temporal['AKUMULASI_PINJAMAN'], 
                    marker='o', linewidth=2, color='darkgreen', markersize=4)
            plt.fill_between(df_temporal['TGL_PARSED'], df_temporal['AKUMULASI_PINJAMAN'], 
                           alpha=0.3, color='lightgreen')
            plt.title("Tren Akumulasi Pinjaman dari Waktu ke Waktu", fontsize=14, fontweight='bold')
            plt.xlabel("Tanggal Jatuh Tempo", fontsize=12)
            plt.ylabel("Akumulasi Pinjaman (Rp)", fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir_vis, f"temporal_akumulasi_{stamp}.png"), dpi=300)
            plt.close()
            
            # === 10. Top Nasabah Berisiko Tinggi ===
            # Kriteria: Jatuh tempo terdekat + nominal besar (top 20)
            df_temporal['DAYS_TO_DUE'] = (df_temporal['TGL_PARSED'] - datetime.datetime.now()).dt.days
            df_risk = df_temporal[df_temporal['DAYS_TO_DUE'] >= 0].copy()  # hanya yang belum jatuh tempo
            df_risk = df_risk.nlargest(20, 'UANG_PINJAMAN')
            
            if len(df_risk) > 0:
                plt.figure(figsize=(14, 8))
                plt.barh(range(len(df_risk)), df_risk['UANG_PINJAMAN'], color='crimson', alpha=0.7)
                plt.yticks(range(len(df_risk)), 
                          [f"{row['NASABAH'][:20]}... ({row['TGL_JATUH_TEMPO']})" 
                           for _, row in df_risk.iterrows()], fontsize=9)
                plt.title("Top 20 Nasabah Berisiko Tinggi (Nominal Besar + Jatuh Tempo Terdekat)", 
                         fontsize=14, fontweight='bold')
                plt.xlabel("Uang Pinjaman (Rp)", fontsize=12)
                plt.grid(axis='x', alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir_vis, f"risk_top_nasabah_{stamp}.png"), dpi=300)
                plt.close()
                
                # Simpan daftar nasabah berisiko ke CSV
                df_risk_export = df_risk[['NO_SBG', 'NASABAH', 'TGL_JATUH_TEMPO', 'UANG_PINJAMAN', 
                                          'CLUSTER_LABEL', 'DAYS_TO_DUE']].copy()
                df_risk_export.to_csv(
                    os.path.join(output_dir_sum, f"risk_top_nasabah_{stamp}.csv"),
                    index=False, encoding='utf-8-sig'
                )

    # ========================================
    # SUMMARY
    # ========================================
    
    summary = []
    summary_rows = []
    for label in label_order:
        group = df[df["CLUSTER_LABEL"] == label]
        rata2 = group["UANG_PINJAMAN"].mean()
        jumlah = len(group)
        persentase = (jumlah / len(df)) * 100
        summary.append(
            f"- {label}: {jumlah} nasabah, rata-rata pinjaman Rp{rata2:,.0f}, mencakup {persentase:.1f}% nasabah."
        )
        summary_rows.append({
            "Segmen": label,
            "Rata-rata Pinjaman (Rp)": round(rata2, 2),
            "Jumlah Nasabah": jumlah,
            "Persentase Nasabah (%)": round(persentase, 2)
        })

    summary_text = "=== Ringkasan Segmen Pinjaman PT Pegadaian ===\n" + "\n".join(summary)
    
    if has_temporal:
        summary_text += f"\n\n=== Ringkasan Temporal ===\n"
        summary_text += f"- Total tanggal jatuh tempo berbeda: {df_temporal['TGL_PARSED'].nunique()}\n"
        summary_text += f"- Rentang tanggal: {df_temporal['TGL_PARSED'].min().strftime('%d-%m-%Y')} s/d {df_temporal['TGL_PARSED'].max().strftime('%d-%m-%Y')}\n"
        summary_text += f"- Total pinjaman keseluruhan: Rp {df_temporal['UANG_PINJAMAN'].sum():,.0f}\n"
        summary_text += f"- Rata-rata pinjaman per hari: Rp {daily_sum.mean():,.0f}\n"
        summary_text += f"- Puncak pinjaman pada: {daily_sum.idxmax().strftime('%d-%m-%Y')} (Rp {daily_sum.max():,.0f})"

    # Simpan summary ke file txt & csv
    with open(os.path.join(output_dir_sum, f"cluster_summary_{stamp}.txt"), "w", encoding="utf-8") as f:
        f.write(summary_text)

    pd.DataFrame(summary_rows).to_csv(
        os.path.join(output_dir_sum, f"cluster_summary_{stamp}.csv"),
        index=False, encoding="utf-8-sig"
    )

    print("\n" + summary_text)
    print(f"\n[OK] Visualisasi disimpan di {output_dir_vis}")
    print(f"[OK] Summary disimpan di {output_dir_sum}")
    
    if has_temporal:
        print(f"[OK] Visualisasi temporal berhasil dibuat")


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, "..", "output", "clustering", "model", "predicted_clusters.csv")
    output_dir_vis = os.path.join(base_dir, "..", "output", "clustering", "visualization")
    output_dir_sum = os.path.join(base_dir, "..", "output", "clustering", "summary")

    run_visualization(input_path, output_dir_vis, output_dir_sum)