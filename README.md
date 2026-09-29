# Automated Invoice Processing and Anomaly Detection

An end-to-end pipeline that takes invoice images and automatically extracts structured data,
validates it against business rules, and flags statistically anomalous invoices using
machine learning — built for the Persevex Machine Learning Internship.

## What it does

1. **Preprocessing** — cleans invoice images (grayscale, blur, binarization) for OCR.
2. **OCR** — extracts text via Tesseract, reconstructing the invoice's table structure
   (line items, columns) from word-level positions rather than reading a flat text block.
3. **Parsing** — pulls structured fields (invoice number, date, vendor, totals, line items)
   from the raw OCR text using regex.
4. **Validation** — deterministic rule checks: quantity × price math, invoice total
   reconciliation, and date logic.
5. **Anomaly Detection** — three ML/statistical techniques: a hybrid per-vendor / dataset-wide
   Z-score on invoice amounts, an Isolation Forest for multivariate outliers, and fuzzy
   duplicate-payment detection.
6. **Output** — one labeled CSV, one row per invoice, with `is_anomaly` and `anomaly_reason`
   columns.

Full methodology and results are documented in [`report/technical_report.pdf`](report/technical_report.pdf).

## Project structure

automated-invoice-processing/
├── data/
│ ├── raw_images/ # input invoice images
│ └── processed/ # output CSVs
├── src/
│ ├── preprocessing.py # image cleanup (OpenCV)
│ ├── ocr_engine.py # text extraction (Tesseract)
│ ├── parser.py # field extraction (regex)
│ ├── validator.py # rule-based validation
│ ├── anomaly_detector.py # Z-score + Isolation Forest + duplicate detection
│ ├── build_dataset.py # runs preprocessing → OCR → parsing → validation on a folder of images
│ └── build_final_output.py # full pipeline entry point — produces the final labeled CSV
├── notebooks/
│ └── exploration.ipynb # visualizations (box plot, scatter plot)
├── report/
│ └── technical_report.pdf
├── requirements.txt
└── README.md

## Setup

**1. Install Python dependencies:**

```bash
pip install -r requirements.txt
```

**2. Install Tesseract OCR** (a system binary, not a Python package):

- **Windows:** download and run the installer from the
  [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) page.
- **macOS:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`

Verify it's installed with `tesseract --version` in your terminal. If `pytesseract` can't
find it automatically on Windows, set the path explicitly at the top of `ocr_engine.py`:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**3. Add invoice images** to `data/raw_images/` (this project was built and tested against the
Kaggle ["High-Quality Invoice Images for OCR"](https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr)
dataset).

## Running the pipeline

Run everything — preprocessing through final labeled CSV — with one command from the project root:

```bash
python src/build_final_output.py
```

This processes every image in `data/raw_images/`, and writes the final labeled dataset to
`data/processed/invoices_final.csv`. By default it processes up to 300 images (see the `limit`
argument in `build_final_output.py` — set it to `None` to process everything).

**To run an individual stage** (useful for debugging one part of the pipeline):

```bash
python src/preprocessing.py    # test image cleanup on one sample image
python src/ocr_engine.py       # test OCR + table extraction on one sample image
python src/parser.py           # test field parsing on 10 sample images
python src/validator.py        # test rule-based validation on one sample image
python src/anomaly_detector.py # run anomaly detection on an already-built dataset
```

**To regenerate the visualizations**, open `notebooks/exploration.ipynb` and run all cells —
it reads `data/processed/invoices_final.csv` and produces the box plot and scatter plot used
in the technical report.

## Output format

`data/processed/invoices_final.csv` — one row per invoice, with:

| Column | Description |
|---|---|
| `file_name`, `invoice_number`, `invoice_date`, `vendor_name`, `total_amount`, `net_total`, `item_count` | Extracted invoice fields |
| `is_valid`, `validation_reason` | Rule-based validation result |
| `zscore`, `is_zscore_anomaly`, `zscore_basis` | Z-score outlier result (per-vendor where history exists, dataset-wide fallback otherwise) |
| `is_isolation_forest_anomaly` | Multivariate outlier result |
| `is_duplicate`, `duplicate_of` | Fuzzy duplicate-payment detection result |
| `has_validation_issue`, `has_statistical_anomaly` | Rule violations and statistical anomalies, kept separate |
| **`is_anomaly`, `anomaly_reason`** | **Required output columns** — `True` if either category above is `True`, with a combined human-readable reason |

## Known limitations

See Section 9 of the technical report for full details. In brief: OCR table-column extraction
is calibrated to this dataset's specific layout and would need recalibration for a different
invoice format; the fixed binarization threshold assumes clean, consistently-lit images.

## Author

Jeet Gajera — Machine Learning Internship, Persevex