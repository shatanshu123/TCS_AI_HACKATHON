# Sample Invoice Dataset

Synthetic test data for the Flask invoice-processing backend.

All names, emails, phone numbers, tax ids, addresses, bank details, and UPI ids in these files are fake. They are intentionally present so the masking layer can prove that raw PII does not enter the LLM prompt.

## Files

```text
sample-dataset/
  invoices/
    invoice-001-standard.pdf
    invoice-002-missing-total.pdf
    invoice-003-usd-services.pdf
    invoice-004-noisy-ocr.pdf
  expected-results.json
  generate_pdf_invoices.py
  upload_samples.ps1
```

## How To Use

Start the backend:

```powershell
$env:PYTHONPATH = ".deps"
python run.py
```

In a second PowerShell window:

```powershell
.\sample-dataset\upload_samples.ps1
```

Or upload one file manually:

```powershell
curl.exe -X POST http://127.0.0.1:5000/api/invoices -F "files=@sample-dataset/invoices/invoice-001-standard.pdf"
```

## What To Check

- `invoice-001-standard.pdf` should complete successfully.
- `invoice-002-missing-total.pdf` should need review because total amount is missing.
- `invoice-003-usd-services.pdf` should complete with USD fields.
- `invoice-004-noisy-ocr.pdf` should need review because the total label is intentionally OCR-noisy.
- Stored masked text should contain tokens such as `[GSTIN_1]`, `[EMAIL_1]`, `[PHONE_1]`, `[CONTACT_LINE_1]`, and `[BANK_ACCOUNT_1]`.

Regenerate the PDFs after editing the synthetic source data:

```powershell
python .\sample-dataset\generate_pdf_invoices.py
```
