import re

from ocr_engine import extract_invoice_items


def normalize_number(value):

    if value is None:
        return None

    value = value.strip()
    value = value.replace("$", "")
    value = value.replace(" ", "")
    value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None

def normalize_percentage(value):

    if value is None:
        return None

    value = value.strip()
    value = value.replace("%", "")
    value = value.replace(" ", "")
    value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None
    
def parse_invoice(raw_text, items):

    # ---------------------------------------------------------
    # 1. EXTRACT INVOICE NUMBER
    # ---------------------------------------------------------

    invoice_number = re.search(
        r"Invoice\s+no[:\s]+(\d+)",
        raw_text,
        re.IGNORECASE
    )

    if invoice_number:
        invoice_number = invoice_number.group(1)
    else:
        invoice_number = None


    # ---------------------------------------------------------
    # 2. EXTRACT INVOICE DATE
    # ---------------------------------------------------------

    DATE_PATTERNS = [
        r"\b\d{2}/\d{2}/\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{2}-\d{2}-\d{4}\b",
    ]

    invoice_date = None
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, raw_text)
        if match:
            invoice_date = match.group(0)
            break

    # ---------------------------------------------------------
    # 3. EXTRACT VENDOR NAME
    # ---------------------------------------------------------

    vendor = re.search(
        r"Seller\s*:\s*(?:Client\s*:\s*)?\n+\s*([^\n]+)",
        raw_text,
        re.IGNORECASE
    )

    if vendor:
        vendor = vendor.group(1).strip()
    else:
        vendor = None


    # ---------------------------------------------------------
    # 4. EXTRACT SUMMARY SECTION
    # ---------------------------------------------------------

    summary = re.search(
        r"SUMMARY(.*)",
        raw_text,
        re.IGNORECASE | re.DOTALL
    )

    if summary:
        summary_text = summary.group(1)
    else:
        summary_text = ""


    # ---------------------------------------------------------
    # 5. EXTRACT FINAL TOTAL AMOUNT
    # ---------------------------------------------------------

    total_match = re.search(
        r"Total\s+\$?\s*[\d,\.\s]+\s+\$?\s*[\d,\.\s]+\s+\$?\s*([\d,\.\s]+)",
        summary_text,
        re.IGNORECASE
    )

    if total_match:
        total_amount = total_match.group(1)

    else:
        gross_matches = list(
            re.finditer(
                r"Gross\s+worth",
                summary_text,
                re.IGNORECASE
            )
        )

        if gross_matches:
            last_gross = gross_matches[-1]

            after_gross = summary_text[last_gross.end():]

            amount_match = re.search(
                r"\$?\s*([\d,\.\s]+)",
                after_gross
            )

            if amount_match:
                total_amount = amount_match.group(1)
            else:
                total_amount = None

        else:
            total_amount = None

    total_amount = normalize_number(total_amount)

    # ---------------------------------------------------------
    # 6. EXTRACT NET TOTAL
    # ---------------------------------------------------------

    net_total_match = re.search(
        r"Net\s+worth\s+VAT\s*\n\s*\$?\s*([\d]+(?:[ ,]\d{3})*(?:[.,]\d{2}))",
        summary_text,
        re.IGNORECASE
    )

    if net_total_match:

        net_total = net_total_match.group(1)

    else:

        net_total_match = re.search(
            r"Net\s+worth\s*\n+\s*\$?\s*([\d]+(?:[ ,]\d{3})*(?:[.,]\d{2}))",
            summary_text,
            re.IGNORECASE
        )

        if net_total_match:
            net_total = net_total_match.group(1)
        else:
            net_total = None

    net_total = normalize_number(net_total)
    
    # ---------------------------------------------------------
    # 7. DISPLAY EXTRACTED INFORMATION
    # ---------------------------------------------------------


    for item in items:

        item["net_price"] = normalize_number(
            item["net_price"]
        )
        item["net_worth"] = normalize_number(
            item["net_worth"]
        )
        item["gross_worth"] = normalize_number(
            item["gross_worth"]
        )
        item["qty"] = normalize_number(
            item["qty"]
        )
        item["vat"] = normalize_percentage(
            item["vat"]
        )       

    # 8. Return the extracted information as a dictionary
    return {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "vendor_name": vendor,
        "total_amount": total_amount,
        "items": items,
        "net_total": net_total,
    }



if __name__ == "__main__":

    import os

    folder_path = "data/raw_images/batch_1/batch_1"

    image_files = []

    for root, dirs, files in os.walk(folder_path):

        for file in files:

            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_files.append(
                    os.path.join(root, file)
                )

    image_files = sorted(image_files)[:10]


    print(f"\nTesting {len(image_files)} invoices...\n")

    for image_file in image_files:

        image_path = image_file

        try:

            result = extract_invoice_items(image_path)

            raw_text = result["raw_text"]
            items = result["items"]

            invoice_data = parse_invoice(
                raw_text,
                items
            )


            print(
                f"✅ PASS: {os.path.basename(image_file)} | "
                f"Net Total: {invoice_data['net_total']} | "
                f"Gross Total: {invoice_data['total_amount']}"
            )

        except Exception as e:

            print(f"❌ FAIL: {os.path.basename(image_file)}")
            print(f"   Error: {e}")