import os
import pandas as pd
from datetime import datetime

from ocr_engine import extract_invoice_items
from parser import parse_invoice
from validator import validate_invoice


DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]


def find_images(folder_path):
    image_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_files.append(os.path.join(root, file))
    return sorted(image_files)


def parse_date_string(date_str):
    if date_str is None:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def extract_and_parse(image_path):
    result = extract_invoice_items(image_path)
    invoice = parse_invoice(result["raw_text"], result["items"])
    return invoice


def build_dataset(folder_path, output_csv, limit=None):
    image_files = find_images(folder_path)

    if limit:
        image_files = image_files[:limit]

    print(f"Processing {len(image_files)} invoices...\n")

    # PASS 1: extract + parse every invoice, and track the most recent date
    parsed_invoices = []
    failures = []
    latest_date = None

    for image_path in image_files:
        try:
            invoice = extract_and_parse(image_path)
            parsed_invoices.append((image_path, invoice))

            invoice_date_obj = parse_date_string(invoice["invoice_date"])
            if invoice_date_obj is not None:
                if latest_date is None or invoice_date_obj > latest_date:
                    latest_date = invoice_date_obj

        except Exception as e:
            failures.append((os.path.basename(image_path), str(e)))
            print(f"FAILED: {os.path.basename(image_path)} -- {e}")

    if latest_date is None:
        raise ValueError("Could not find any valid invoice date in the dataset.")

    print(f"\nUsing {latest_date} as the reference 'most recent' date.\n")

    # PASS 2: validate each invoice against that reference date
    rows = []
    for image_path, invoice in parsed_invoices:
        validation = validate_invoice(invoice, latest_date)

        rows.append({
            "file_name": os.path.basename(image_path),
            "invoice_number": invoice["invoice_number"],
            "invoice_date": invoice["invoice_date"],
            "vendor_name": invoice["vendor_name"],
            "total_amount": invoice["total_amount"],
            "net_total": invoice["net_total"],
            "item_count": len(invoice["items"]),
            "is_valid": validation["is_valid"],
            "validation_reason": validation["reason"],
        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)

    print(f"Done. {len(rows)} succeeded, {len(failures)} failed.")
    print(f"Saved to {output_csv}")

    return df


if __name__ == "__main__":
    folder_path = "data/raw_images"
    output_csv = "data/processed/invoices.csv"

    df = build_dataset(folder_path, output_csv, limit=300)
    print(df.head())