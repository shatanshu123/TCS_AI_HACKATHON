# Invoice Processing Assistant Backend

Flask backend for the "Technology Back Office Automated Invoice Processing Assistant" problem statement.

The system accepts invoice uploads, extracts text locally, masks personal information before any LLM call, extracts key invoice fields, validates them, and stores all artifacts on the local filesystem plus SQLite.

## Privacy Boundary

Raw invoice data never goes directly to an LLM.

Pipeline:

1. Upload invoice to local storage.
2. Extract OCR/text locally.
3. Mask PII and sensitive identifiers into deterministic tokens.
4. Run a leakage guard on the masked payload.
5. Send only masked text to the extraction client.
6. Store token mapping locally for reviewer/audit use.

Masked examples:

- `john@example.com` -> `[EMAIL_1]`
- `+91 9876543210` -> `[PHONE_1]`
- `ABCDE1234F` -> `[PAN_1]`
- `29ABCDE1234F1Z5` -> `[GSTIN_1]`
- bank account numbers, UPI ids, Aadhaar numbers, address/contact lines -> masked tokens

## Project Structure

```text
app/
  __init__.py
  config.py
  routes.py
  storage.py
  services/
    extractor.py
    llm_client.py
    ocr.py
    pii_masker.py
    validator.py
run.py
tests/
  test_pii_masker.py
  test_api.py
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

The API starts on `http://127.0.0.1:5000`.

## Using Your API Key

Do not paste the key into source code or chat logs. Put it in a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4.1-mini
```

The OpenAI provider still receives only masked OCR text. If the key is missing, dependencies are unavailable, or the provider call fails, the backend records a warning and falls back to the deterministic local extractor using the already-masked text.

For the event GenAI Lab endpoint, use the LangChain-compatible provider:

```text
LLM_PROVIDER=genailab
GENAILAB_BASE_URL=https://genailab.tcs.in
GENAILAB_MODEL=azure_ai/genailab-maas-DeepSeek-V3-0324
GENAILAB_API_KEY=sk-your-key-here
GENAILAB_VERIFY_SSL=false
```

Internally this constructs the client in the same style as the event snippet:

```python
http_client = httpx.Client(verify=False)
llm = ChatOpenAI(
    base_url=GENAILAB_BASE_URL,
    model=GENAILAB_MODEL,
    api_key=GENAILAB_API_KEY,
    http_client=http_client,
)
```

The privacy rule is unchanged: only masked OCR text is passed to `llm.invoke(...)`.

## API

### Health

```http
GET /health
```

### Upload A Batch

```http
POST /api/invoices
Content-Type: multipart/form-data

files=<one or more pdf/png/jpg/txt invoices>
```

For local testing without OCR binaries, send a text invoice:

```powershell
curl.exe -X POST http://127.0.0.1:5000/api/invoices `
  -F "files=@sample-invoice.txt"
```

### List Invoices

```http
GET /api/invoices
```

### Get Invoice

```http
GET /api/invoices/<invoice_id>
```

### Reviewer Corrections

```http
PATCH /api/invoices/<invoice_id>/review
Content-Type: application/json

{
  "fields": {
    "vendor": "Acme Supplies",
    "total_amount": 1234.56
  },
  "reviewed_by": "finance.user"
}
```

## Notes

- PDF extraction uses `pypdf` when installed.
- Image OCR uses `pytesseract` and `Pillow` when installed and when the Tesseract binary is available.
- If optional OCR dependencies are missing, the upload is still stored and the response includes a warning.
- `LLM_PROVIDER=local` uses the deterministic local extractor. This is the default and is safe for demos.
