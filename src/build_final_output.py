import pandas as pd

from build_dataset import build_dataset
from anomaly_detector import run_anomaly_detection


def combine_anomaly_reasons(row):
    reasons = []

    if row.get("is_zscore_anomaly"):
        reasons.append(f"Statistical outlier on total amount (z={row['zscore']:.2f})")

    if row.get("is_isolation_forest_anomaly"):
        reasons.append("Unusual combination of amount/item features (Isolation Forest)")

    if row.get("is_duplicate"):
        reasons.append(f"Possible duplicate of {row['duplicate_of']}")

    return "; ".join(reasons) if reasons else None


def build_final_dataset(raw_images_folder, output_csv, limit=None):
    df = build_dataset(raw_images_folder, output_csv, limit=limit)
    df = run_anomaly_detection(df)

    # Keep validation and statistical anomaly detection as separate signals
    df["has_validation_issue"] = ~df["is_valid"]

    df["has_statistical_anomaly"] = (
        df["is_zscore_anomaly"].fillna(False)
        | df["is_isolation_forest_anomaly"].fillna(False)
        | df["is_duplicate"].fillna(False)
    )

    # Required by the project brief: overall True/False anomaly flag
    df["is_anomaly"] = df["has_validation_issue"] | df["has_statistical_anomaly"]

    # Required by the project brief: combined reason, but built from both sources separately
    df["anomaly_reason"] = df.apply(
        lambda row: "; ".join(
            filter(None, [
                row["validation_reason"] if row["has_validation_issue"] else None,
                combine_anomaly_reasons(row) if row["has_statistical_anomaly"] else None,
            ])
        ) or None,
        axis=1
    )

    df.to_csv(output_csv, index=False)

    print(f"\nFinal dataset saved to {output_csv}")
    print(f"Validation issues: {df['has_validation_issue'].sum()} / {len(df)}")
    print(f"Statistical anomalies (Z-score/Isolation Forest/duplicate): {df['has_statistical_anomaly'].sum()} / {len(df)}")
    print(f"Total is_anomaly (either): {df['is_anomaly'].sum()} / {len(df)}")

    return df


if __name__ == "__main__":
    raw_images_folder = "data/raw_images"
    output_csv = "data/processed/invoices_final.csv"

    df = build_final_dataset(raw_images_folder, output_csv, limit=300)