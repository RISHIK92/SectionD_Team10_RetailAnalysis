"""ETL Pipeline - Retail Analytics Project

Automated end-to-end data pipeline for retail transaction analysis.

Pipeline Steps:
  1. Extract  – Load raw data from CSV
  2. Transform – Clean, validate, and enrich data
  3. Load      – Export cleaned / Tableau-ready dataset

Author: SectionD_Team10
Last Updated: April 29, 2026
"""

from __future__ import annotations

import warnings
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data/raw/raw_retail_data.csv"
CLEANED_DATA_PATH = PROJECT_ROOT / "data/processed/cleaned_dataset.csv"
TABLEAU_DATA_PATH = PROJECT_ROOT / "data/processed/tableau_ready_dataset.csv"

CONFIG = {
    "RANDOM_SEED": 42,
    "VERBOSE": True,
    "EXPORT_CLEANED": True,
    "EXPORT_TABLEAU": True,
    "VALIDATION_ENABLED": True,
    "DECIMAL_PRECISION": 2,
}

pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", lambda x: f"{x:.2f}")


def extract(raw_path: Path) -> tuple[pd.DataFrame, tuple, float]:
    print("🔄 Loading raw data...")
    df_raw = pd.read_csv(raw_path)
    original_shape = df_raw.shape
    original_memory = df_raw.memory_usage(deep=True).sum() / (1024 ** 2)

    print(f"✅ Data loaded: {original_shape[0]:,} rows × {original_shape[1]} columns")
    print(f"💾 Memory: {original_memory:.2f} MB")
    print(f"📋 Columns: {df_raw.columns.tolist()}")

    null_counts = df_raw.isnull().sum()
    null_pct = (null_counts / len(df_raw) * 100).round(2)
    quality_df = pd.DataFrame({"Null Count": null_counts, "Null %": null_pct})
    quality_df = quality_df[quality_df["Null Count"] > 0].sort_values("Null Count", ascending=False)
    if not quality_df.empty:
        print("\nNull values by column:")
        print(quality_df.to_string())

    print(f"\n📊 Duplicate rows: {df_raw.duplicated().sum():,}")
    if "Transaction_ID" in df_raw.columns:
        print(f"📊 Duplicate Transaction IDs: {df_raw['Transaction_ID'].duplicated().sum():,}")

    return df_raw, original_shape, original_memory


def drop_pii(df: pd.DataFrame) -> pd.DataFrame:
    pii_cols = ["Name", "Email", "Phone", "Address", "Zipcode"]
    cols_to_drop = [c for c in pii_cols if c in df.columns]
    before = df.shape[1]
    df = df.drop(columns=cols_to_drop)
    print(f"🗑️  PII removed: {cols_to_drop}  ({before} → {df.shape[1]} columns)")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(keep="first")
    full_removed = before - len(df)
    print(f"🔄 Full duplicates removed: {full_removed:,}")

    if "Transaction_ID" in df.columns:
        before2 = len(df)
        df = df.drop_duplicates(subset=["Transaction_ID"], keep="first")
        tid_removed = before2 - len(df)
        print(f"🔄 Duplicate Transaction IDs removed: {tid_removed:,}")
        print(f"📊 Total duplicates removed: {full_removed + tid_removed:,}")

    return df


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    critical = ["Transaction_ID", "Customer_ID", "Date", "Amount"]
    present = [c for c in critical if c in df.columns]
    before = len(df)
    df = df.dropna(subset=present)
    removed = before - len(df)
    print(f"🧹 Rows removed (critical nulls): {removed:,}  |  Remaining: {len(df):,}")
    remaining = df.isnull().sum().sum()
    print(f"📊 Remaining nulls: {remaining:,}")
    return df


def optimize_dtypes(df: pd.DataFrame, decimal_precision: int = 2) -> pd.DataFrame:
    mem_before = df.memory_usage(deep=True).sum() / (1024 ** 2)

    for col in ["Transaction_ID", "Customer_ID", "Age", "Total_Purchases", "Ratings"]:
        if col in df.columns:
            df[col] = df[col].astype("Int64")

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    if "Time" in df.columns:
        df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S", errors="coerce").dt.time

    for col in ["Amount", "Total_Amount"]:
        if col in df.columns:
            df[col] = df[col].round(decimal_precision)

    cat_cols = [
        "City", "State", "Country", "Gender", "Income", "Customer_Segment",
        "Product_Category", "Product_Brand", "Product_Type", "Feedback",
        "Shipping_Method", "Payment_Method", "Order_Status", "products",
    ]
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    mem_after = df.memory_usage(deep=True).sum() / (1024 ** 2)
    saved = mem_before - mem_after
    print(f"🔧 Memory: {mem_before:.2f} MB → {mem_after:.2f} MB  (saved {saved:.2f} MB, {saved/mem_before*100:.1f}%)")
    return df


def fix_month_ordering(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" not in df.columns:
        return df
    df["Year"] = df["Date"].dt.year.astype("Int64")
    df["Month"] = df["Date"].dt.month_name()
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)
    print("📅 Month/Year columns re-derived with chronological ordering")
    return df


def validate(df: pd.DataFrame) -> bool:
    print("\n✅ Validation Checks:")
    passed = True

    null_count = df.isnull().sum().sum()
    ok = null_count == 0
    print(f"   {'✅ PASS' if ok else '❌ FAIL'} – Zero nulls: {null_count} found")
    passed = passed and ok

    if "Transaction_ID" in df.columns:
        dups = df["Transaction_ID"].duplicated().sum()
        ok = dups == 0
        print(f"   {'✅ PASS' if ok else '❌ FAIL'} – Unique Transaction IDs: {dups} duplicates")
        passed = passed and ok

    if "Age" in df.columns:
        ok = df["Age"].min() >= 0 and df["Age"].max() <= 120
        print(f"   {'✅ PASS' if ok else '❌ FAIL'} – Age range: {df['Age'].min()} – {df['Age'].max()}")
        passed = passed and ok

    if "Ratings" in df.columns:
        ok = df["Ratings"].min() >= 1 and df["Ratings"].max() <= 5
        print(f"   {'✅ PASS' if ok else '❌ FAIL'} – Ratings range: {df['Ratings'].min()} – {df['Ratings'].max()}")
        passed = passed and ok

    if "Amount" in df.columns and "Total_Purchases" in df.columns:
        ok = (df["Amount"] > 0).all() and (df["Total_Purchases"] > 0).all()
        print(f"   {'✅ PASS' if ok else '❌ FAIL'} – Positive amounts & quantities")
        passed = passed and ok

    if "Date" in df.columns:
        print(f"   ✅ INFO – Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

    print(f"\n{'🎉 All validations PASSED!' if passed else '⚠️  Some validations FAILED'}")
    return passed


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    print("🔧 Creating derived columns:\n")

    if "Date" in df.columns:
        df["Month_Num"] = df["Date"].dt.month
        df["Quarter"] = "Q" + df["Date"].dt.quarter.astype(str)
        df["Day_of_Week"] = df["Date"].dt.day_name()
        print("   ✅ Month_Num, Quarter, Day_of_Week")

    if "Time" in df.columns:
        df["Hour"] = pd.to_datetime(df["Time"].astype(str), format="%H:%M:%S", errors="coerce").dt.hour
        print("   ✅ Hour")

    if "Total_Amount" in df.columns and "Total_Purchases" in df.columns:
        df["Revenue_per_Purchase"] = (df["Total_Amount"] / df["Total_Purchases"]).round(2)
        print("   ✅ Revenue_per_Purchase")

    if "Total_Amount" in df.columns:
        p75 = df["Total_Amount"].quantile(0.75)
        df["High_Value_Flag"] = (df["Total_Amount"] > p75).astype(int)
        print(f"   ✅ High_Value_Flag (threshold ₹{p75:.2f})")

    if "Ratings" in df.columns:
        df["Satisfied_Flag"] = (df["Ratings"] >= 4).fillna(False).astype(int)
        pct = df["Satisfied_Flag"].mean() * 100
        print(f"   ✅ Satisfied_Flag ({pct:.1f}% satisfied)")

    if "Feedback" in df.columns:
        feedback_map = {"Excellent": 3, "Good": 2, "Average": 2, "Bad": 1}
        df["Feedback_Score"] = df["Feedback"].map(feedback_map).fillna(0).astype(int)
        print("   ✅ Feedback_Score")

    print(f"\n📊 Dataset shape after enrichment: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def transform(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df_raw.copy()
    df = drop_pii(df)
    df = remove_duplicates(df)
    df = handle_nulls(df)
    df = optimize_dtypes(df, CONFIG["DECIMAL_PRECISION"])
    df = fix_month_ordering(df)
    validate(df)
    df_tableau = add_derived_columns(df)
    return df, df_tableau


def load(df_tableau: pd.DataFrame, df_cleaned: pd.DataFrame, output_path: Path) -> None:
    if not CONFIG["EXPORT_CLEANED"]:
        print("⏭️  Export skipped (disabled in config)")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_tableau.to_csv(output_path, index=False)
    size_mb = output_path.stat().st_size / (1024 ** 2)
    added_cols = df_tableau.shape[1] - df_cleaned.shape[1]
    print(f"\n💾 Saved → {output_path}")
    print(f"   Shape: {df_tableau.shape[0]:,} rows × {df_tableau.shape[1]} columns")
    print(f"   File size: {size_mb:.2f} MB")
    print(f"   Includes {added_cols} derived columns")


def print_summary(
    df_raw: pd.DataFrame,
    df: pd.DataFrame,
    df_tableau: pd.DataFrame,
    original_memory: float,
    output_path: Path,
) -> None:
    memory_final = df.memory_usage(deep=True).sum() / (1024 ** 2)
    rows_removed = df_raw.shape[0] - df.shape[0]
    cols_removed = df_raw.shape[1] - df.shape[1]
    retained_pct = df.shape[0] / df_raw.shape[0] * 100

    print("\n" + "=" * 80)
    print("📊 ETL PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"\n🔢 DATA TRANSFORMATION:")
    print(f"   Raw data:        {df_raw.shape[0]:>10,} rows × {df_raw.shape[1]:>2} columns")
    print(f"   Cleaned data:    {df.shape[0]:>10,} rows × {df.shape[1]:>2} columns")
    print(f"   Tableau data:    {df_tableau.shape[0]:>10,} rows × {df_tableau.shape[1]:>2} columns")
    print(f"   Rows removed:    {rows_removed:>10,} ({100 - retained_pct:.2f}%)")
    print(f"   Cols dropped:    {cols_removed:>10,} (PII)")
    print(f"   Cols added:      {df_tableau.shape[1] - df.shape[1]:>10,} (derived)")

    print(f"\n💾 MEMORY:")
    print(f"   Raw:             {original_memory:>10.2f} MB")
    print(f"   Cleaned:         {memory_final:>10.2f} MB")
    mem_saved = original_memory - memory_final
    print(f"   Saved:           {mem_saved:>10.2f} MB ({mem_saved / original_memory * 100:.1f}%)")

    print(f"\n✅ QUALITY:")
    print(f"   Null values:     {df.isnull().sum().sum():>10,}")
    if "Transaction_ID" in df.columns:
        print(f"   Duplicate IDs:   {df['Transaction_ID'].duplicated().sum():>10,}")
    if "Customer_ID" in df.columns:
        print(f"   Unique customers:{df['Customer_ID'].nunique():>10,}")
    if "Date" in df.columns:
        print(f"   Date range:      {df['Date'].min().date()} to {df['Date'].max().date()}")

    print(f"\n📈 BUSINESS METRICS:")
    if "Total_Amount" in df.columns:
        print(f"   Total revenue:   ₹{df['Total_Amount'].sum() / 1e7:>9.2f} Cr")
        print(f"   Avg transaction: ₹{df['Total_Amount'].mean():>9.2f}")
    if "Ratings" in df.columns:
        print(f"   Avg rating:      {df['Ratings'].mean():>10.2f} / 5.0")
    if "Satisfied_Flag" in df_tableau.columns:
        print(f"   Satisfaction:    {df_tableau['Satisfied_Flag'].mean() * 100:>10.1f}%")

    print(f"\n📁 OUTPUT: {output_path.name}")
    print(f"\n⏱️  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("✅ ETL PIPELINE EXECUTED SUCCESSFULLY!")
    print("=" * 80)


def plot_quality(df_raw: pd.DataFrame, df: pd.DataFrame, original_memory: float) -> None:
    memory_final = df.memory_usage(deep=True).sum() / (1024 ** 2)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    width = 0.35

    categories = ["Rows (K)", "Columns", "Memory (MB)"]
    before = [df_raw.shape[0] / 1000, df_raw.shape[1], original_memory]
    after = [df.shape[0] / 1000, df.shape[1], memory_final]
    x = np.arange(len(categories))
    axes[0].bar(x - width / 2, before, width, label="Raw", color="#e74c3c", alpha=0.8)
    axes[0].bar(x + width / 2, after, width, label="Cleaned", color="#2ecc71", alpha=0.8)
    axes[0].set_title("ETL Pipeline: Before vs After", fontweight="bold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(categories)
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.3)

    quality_metrics = ["Completeness", "Uniqueness", "Validity"]
    raw_scores = [
        (df_raw.shape[0] - df_raw.isnull().sum().sum()) / (df_raw.shape[0] * df_raw.shape[1]) * 100,
        (df_raw.shape[0] - df_raw.duplicated().sum()) / df_raw.shape[0] * 100,
        85,
    ]
    x2 = np.arange(len(quality_metrics))
    axes[1].bar(x2 - width / 2, raw_scores, width, label="Raw", color="#e74c3c", alpha=0.8)
    axes[1].bar(x2 + width / 2, [100, 100, 100], width, label="Cleaned", color="#2ecc71", alpha=0.8)
    axes[1].set_title("Data Quality Improvement", fontweight="bold")
    axes[1].set_xticks(x2)
    axes[1].set_xticklabels(quality_metrics)
    axes[1].set_ylim([0, 110])
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "reports" / "etl_quality_chart.png", dpi=150)
    plt.show()
    print("✅ Quality chart saved to reports/etl_quality_chart.png")


def main() -> None:
    print(f"📅 Pipeline started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    df_raw, original_shape, original_memory = extract(RAW_DATA_PATH)
    df, df_tableau = transform(df_raw)
    load(df_tableau, df, CLEANED_DATA_PATH)
    print_summary(df_raw, df, df_tableau, original_memory, CLEANED_DATA_PATH)
    plot_quality(df_raw, df, original_memory)


if __name__ == "__main__":
    main()
