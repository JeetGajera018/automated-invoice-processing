from datetime import datetime, date

from ocr_engine import extract_invoice_items

from parser import parse_invoice

def validate_item_math(item):

    if item["qty"] is None or item["net_price"] is None:
        return {"is_valid": False, "reason": "Missing data"}

    expected_net_worth = item["qty"] * item["net_price"]

    actual_net_worth = item["net_worth"]

    difference = abs(
        expected_net_worth - actual_net_worth
    )

    if difference < 0.01:
        return {
            "is_valid": True,
            "reason": None
        }

    else:
        return {
            "is_valid": False,
            "reason": "Quantity × Unit Price does not equal Net Worth"
        }

def validate_invoice_net_total(invoice):

    actual_net_total = invoice["net_total"]

    if actual_net_total is None:
        return {
            "is_valid": False,
            "reason": "Missing net_total — could not extract from OCR"
        }

    calculated_net_total = sum(
        item["net_worth"]
        for item in invoice["items"]
        if item["net_worth"] is not None
    )


    difference = abs(
        calculated_net_total - actual_net_total
    )

    if difference < 0.01:
        return {
            "is_valid": True,
            "reason": None
        }

    else:
        return {
            "is_valid": False,
            "reason": "Sum of item Net Worth does not equal Invoice Net Total"
        }

def date_validation(invoice, reference_date):
    invoice_date = invoice["invoice_date"]

    if invoice_date is None:
        return {
            "is_valid": False,
            "reason": "Missing invoice_date — could not extract from OCR"
        }

    DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]

    invoice_date_obj = None
    for fmt in DATE_FORMATS:
        try:
            invoice_date_obj = datetime.strptime(invoice_date, fmt).date()
            break
        except ValueError:
            continue

    if invoice_date_obj is None:
        return {
            "is_valid": False,
            "reason": f"Could not parse date format: {invoice_date}"
        }

    difference = (reference_date - invoice_date_obj).days

    if invoice_date_obj > reference_date:
        return {
            "is_valid": False,
            "reason": "Invoice date is after the dataset's most recent date"
        }
    else:
        if difference > 90:
            return {
                "is_valid": False,
                "reason": "Invoice date is older than 90 days relative to the dataset"
            }
        else:
            return {
                "is_valid": True,
                "reason": None
            }
        
def validate_invoice_gross_total(invoice):

    actual_gross_total = invoice["total_amount"]

    if actual_gross_total is None:
        return {
            "is_valid": False,
            "reason": "Missing total_amount — could not extract from OCR"
        }

    calculated_gross_total = 0

    for item in invoice["items"]:
        if item["net_worth"] is None or item["vat"] is None:
            continue
        vat_amount = item["net_worth"] * item["vat"] / 100
        gross_amount = item["net_worth"] + vat_amount

        calculated_gross_total += gross_amount

    difference = abs(
        calculated_gross_total - actual_gross_total
    )

    if difference < 0.01:
        return {
            "is_valid": True,
            "reason": None
        }

    else:
        return {
            "is_valid": False,
            "reason": "Sum of item Gross Amount does not equal Invoice Gross Total"
        }



def validate_invoice(invoice, reference_date):
    item_validation_results = [
        validate_item_math(item)
        for item in invoice["items"]
    ]
    net_total_result = validate_invoice_net_total(invoice)
    date_result = date_validation(invoice, reference_date)
    gross_total_result = validate_invoice_gross_total(invoice)

    if net_total_result["is_valid"] and date_result["is_valid"] and gross_total_result["is_valid"] and all(result["is_valid"] for result in item_validation_results):
        return {
            "is_valid": True,
            "reason": None
        }
    invalid_reasons = []
    if not net_total_result["is_valid"]:
        invalid_reasons.append(net_total_result["reason"])
    if not date_result["is_valid"]:
        invalid_reasons.append(date_result["reason"])
    if not gross_total_result["is_valid"]:
        invalid_reasons.append(gross_total_result["reason"])
    if not all(result["is_valid"] for result in item_validation_results):
        invalid_reasons.extend([
            result["reason"]
            for result in item_validation_results
            if not result["is_valid"]
        ])

    return {
        "is_valid": False,
        "reason": f"Invalid invoice: {', '.join(invalid_reasons)}"
    }

if __name__ == "__main__":

    image_path = "data/raw_images/batch_1/batch_1/batch1_3/batch1-1488.jpg"
    result = extract_invoice_items(image_path)
    invoice = parse_invoice(
        result["raw_text"],
        result["items"]
    )
    validation = validate_invoice(invoice, date.today())
    print("Validation result:", validation)
    