import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from rapidfuzz import fuzz


def add_zscore_anomaly(df, column="total_amount", vendor_column="vendor_name", threshold=2.5):
    df = df.copy()

    valid_mask = df[column].notna() & (df[column] > 0)
    df["log_amount"] = np.nan
    df.loc[valid_mask, "log_amount"] = np.log(df.loc[valid_mask, column])
    vendor_mean = df.groupby(vendor_column)["log_amount"].transform("mean")
    vendor_std = df.groupby(vendor_column)["log_amount"].transform("std")
    has_vendor_history = valid_mask & vendor_std.notna() & (vendor_std > 0)
    global_mean = df.loc[valid_mask, "log_amount"].mean()
    global_std = df.loc[valid_mask, "log_amount"].std()

    df["zscore"] = np.nan
    df["zscore_basis"] = None

    df.loc[has_vendor_history, "zscore"] = (
        (df.loc[has_vendor_history, "log_amount"] - vendor_mean.loc[has_vendor_history])
        / vendor_std.loc[has_vendor_history]
    )
    df.loc[has_vendor_history, "zscore_basis"] = "per_vendor"

    fallback_mask = valid_mask & ~has_vendor_history
    df.loc[fallback_mask, "zscore"] = (
        (df.loc[fallback_mask, "log_amount"] - global_mean) / global_std
    )
    df.loc[fallback_mask, "zscore_basis"] = "dataset_wide_fallback"

    df["is_zscore_anomaly"] = df["zscore"].abs() > threshold
    df.drop(columns=["log_amount"], inplace=True)

    return df


def add_isolation_forest_anomaly(df, contamination=0.05):
    df = df.copy()
    features = ["total_amount", "net_total", "item_count"]

    valid_mask = df[features].notna().all(axis=1)
    X = df.loc[valid_mask, features]

    model = IsolationForest(contamination=contamination, random_state=42)
    preds = model.fit_predict(X)

    df["is_isolation_forest_anomaly"] = False
    df.loc[valid_mask, "is_isolation_forest_anomaly"] = preds == -1
    return df


def add_duplicate_detection(df, number_threshold=90, amount_tolerance=0.02):
    df = df.copy()
    df["is_duplicate"] = False
    df["duplicate_of"] = None

    valid = df[df["invoice_number"].notna() & df["total_amount"].notna()].copy()

    for i, row_a in valid.iterrows():
        for j, row_b in valid.iterrows():
            if i >= j:
                continue
            num_similarity = fuzz.ratio(str(row_a["invoice_number"]), str(row_b["invoice_number"]))
            amount_a, amount_b = row_a["total_amount"], row_b["total_amount"]
            amount_close = abs(amount_a - amount_b) <= amount_tolerance * max(amount_a, amount_b)

            if num_similarity >= number_threshold and amount_close:
                df.loc[i, "is_duplicate"] = True
                df.loc[j, "is_duplicate"] = True
                df.loc[j, "duplicate_of"] = row_a["file_name"]

    return df


def run_anomaly_detection(df):
    df = add_zscore_anomaly(df)
    df = add_isolation_forest_anomaly(df)
    df = add_duplicate_detection(df)
    return df


if __name__ == "__main__":
    df = pd.read_csv("data/processed/invoices.csv")
    df = run_anomaly_detection(df)

    print(f"Z-score anomalies: {df['is_zscore_anomaly'].sum()}")
    print(f"Isolation Forest anomalies: {df['is_isolation_forest_anomaly'].sum()}")
    print(f"Duplicates: {df['is_duplicate'].sum()}")

    df.to_csv("data/processed/invoices_with_anomalies.csv", index=False)
    print("\nSaved invoices_with_anomalies.csv")