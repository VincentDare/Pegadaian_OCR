# visualize.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime

def run_visualization(input_path, output_dir_vis, output_dir_sum):
    """
    Visualisasi hasil clustering untuk PT Pegadaian:
    - Mapping cluster otomatis: Pinjaman Kecil → Menengah → Besar
    - Visualisasi: Bar chart (jumlah & rata-rata), Boxplot, Histogram, Pie chart
    - Summary friendly + CSV di folder terpisah
    """
    # Load data
    df = pd.read_csv(input_path)

    # === Tentukan urutan cluster otomatis (dari rata-rata kecil ke besar) ===
    cluster_order = (
        df.groupby("CLUSTER")["UANG_PINJAMAN"]
        .mean()
        .sort_values()
        .index.tolist()
    )

    CLUSTER_LABELS = {
        cluster_order[0]: "Pinjaman Kecil",
        cluster_order[1]: "Pinjaman Menengah",
        cluster_order[2]: "Pinjaman Besar",
    }

    # Mapping label cluster
    df["CLUSTER_LABEL"] = df["CLUSTER"].map(CLUSTER_LABELS)

    # Pastikan folder output ada
    os.makedirs(output_dir_vis, exist_ok=True)
    os.makedirs(output_dir_sum, exist_ok=True)

    # === Timestamp biar file tidak ketimpa ===
    stamp = datetime.datetime.now().strftime("%Y%m%d")

    # === 1. Barplot rata-rata pinjaman per cluster ===
    cluster_means = (
        df.groupby("CLUSTER_LABEL")["UANG_PINJAMAN"]
        .mean()
        .reindex(["Pinjaman Kecil", "Pinjaman Menengah", "Pinjaman Besar"])
    )
    plt.figure(figsize=(8, 5))
    sns.barplot(
        x=cluster_means.index,
        y=cluster_means.values,
        hue=cluster_means.index,
        legend=False,
        palette="viridis"
    )
    plt.title("Rata-rata Pinjaman per Segmen", fontsize=14)
    plt.xlabel("Segmen Nasabah", fontsize=12)
    plt.ylabel("Rata-rata Pinjaman (Rp)", fontsize=12)
    plt.xticks(rotation=0)
    for i, v in enumerate(cluster_means.values):
        plt.text(i, v, f"Rp{v:,.0f}", ha="center", va="bottom", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_bar_{stamp}.png"))
    plt.close()

    # === 1b. Barplot jumlah nasabah per cluster ===
    cluster_counts_abs = df["CLUSTER_LABEL"].value_counts().reindex(
        ["Pinjaman Kecil", "Pinjaman Menengah", "Pinjaman Besar"]
    )
    plt.figure(figsize=(8, 5))
    sns.barplot(
        x=cluster_counts_abs.index,
        y=cluster_counts_abs.values,
        hue=cluster_counts_abs.index,
        legend=False,
        palette="Blues"
    )
    plt.title("Jumlah Nasabah per Segmen", fontsize=14)
    plt.xlabel("Segmen Nasabah", fontsize=12)
    plt.ylabel("Jumlah Nasabah", fontsize=12)
    for i, v in enumerate(cluster_counts_abs.values):
        plt.text(i, v, str(v), ha="center", va="bottom", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_count_bar_{stamp}.png"))
    plt.close()

    # === 2. Boxplot distribusi pinjaman ===
    plt.figure(figsize=(8, 5))
    sns.boxplot(
        x="CLUSTER_LABEL",
        y="UANG_PINJAMAN",
        data=df,
        hue="CLUSTER_LABEL",
        order=["Pinjaman Kecil", "Pinjaman Menengah", "Pinjaman Besar"],
        legend=False,
        palette="Set2"
    )
    plt.title("Distribusi Pinjaman per Segmen (Boxplot)", fontsize=14)
    plt.xlabel("Segmen Nasabah", fontsize=12)
    plt.ylabel("Nilai Pinjaman (Rp)", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_boxplot_{stamp}.png"))
    plt.close()

    # === 3. Histogram distribusi pinjaman ===
    plt.figure(figsize=(10, 6))
    sns.histplot(
        data=df,
        x="UANG_PINJAMAN",
        hue="CLUSTER_LABEL",
        bins=30,
        kde=True,
        multiple="stack",
        hue_order=["Pinjaman Kecil", "Pinjaman Menengah", "Pinjaman Besar"]
    )
    plt.title("Sebaran Pinjaman per Segmen (Histogram)", fontsize=14)
    plt.xlabel("Uang Pinjaman (Rp)", fontsize=12)
    plt.ylabel("Jumlah Nasabah", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_histogram_{stamp}.png"))
    plt.close()

    # === 4. Pie chart distribusi nasabah ===
    cluster_counts = (
        df["CLUSTER_LABEL"].value_counts(normalize=True)
        .reindex(["Pinjaman Kecil", "Pinjaman Menengah", "Pinjaman Besar"]) * 100
    )
    plt.figure(figsize=(6, 6))
    plt.pie(
        cluster_counts,
        labels=cluster_counts.index,
        autopct="%.1f%%",
        colors=sns.color_palette("pastel"),
        startangle=90
    )
    plt.title(" Distribusi Nasabah per Segmen", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir_vis, f"cluster_pie_{stamp}.png"))
    plt.close()

    # === Summary friendly ===
    summary = []
    summary_rows = []
    for label in ["Pinjaman Kecil", "Pinjaman Menengah", "Pinjaman Besar"]:
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

    summary_text = "Ringkasan Segmen Pinjaman PT Pegadaian:\n" + "\n".join(summary)

    # Simpan summary ke file txt & csv (pakai timestamp juga)
    with open(os.path.join(output_dir_sum, f"cluster_summary_{stamp}.txt"), "w", encoding="utf-8") as f:
        f.write(summary_text)

    pd.DataFrame(summary_rows).to_csv(
        os.path.join(output_dir_sum, f"cluster_summary_{stamp}.csv"),
        index=False, encoding="utf-8-sig"
    )

    print(summary_text)
    print(f"✅ Visualisasi disimpan di {output_dir_vis}")
    print(f"✅ Summary disimpan di {output_dir_sum}")


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, "..", "output", "clustering", "model", "clustered_data.csv")
    output_dir_vis = os.path.join(base_dir, "..", "output", "clustering", "visualization")
    output_dir_sum = os.path.join(base_dir, "..", "output", "clustering", "summary")

    run_visualization(input_path, output_dir_vis, output_dir_sum)
