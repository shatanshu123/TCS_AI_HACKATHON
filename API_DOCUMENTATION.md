# Invoice Processing API Documentation

## Overview
This API provides endpoints for processing, extracting, validating, and reviewing invoice documents. The service includes OCR (Optical Character Recognition), LLM-based extraction, PII masking, and confidence analysis capabilities.

---

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check if the service is healthy and operational.

**Request:** No payload required.

**Response (200):**
```json
{
  "status": "ok",
  "service": "invoice-processing-backend"
}
```

---

### 2. Upload Invoices (Synchronous)

**Endpoint:** `POST /api/invoices`

**Description:** Upload one or more invoice files for immediate processing.

**Request Headers:**
- `Content-Type: multipart/form-data`

**Request Payload:**
- Form parameter: `files` (or `file`) - Multiple PDF/image files

**Response (201):**
```json
{
  "count": 2,
  "invoices": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "original_filename": "invoice_001.pdf",
      "stored_filename": "550e8400-e29b-41d4-a716-446655440000-invoice_001.pdf",
      "status": "completed",
      "upload_path": "/path/to/upload/file",
      "ocr_text_path": "/path/to/ocr/text",
      "masked_text_path": "/path/to/masked/text",
      "pii_map_path": "/path/to/pii/map",
      "file_size": 245632,
      "content_type": "application/pdf",
      "extraction": {
        "invoice_number": {
          "value": "INV-2024-001",
          "confidence": 0.95,
          "source": "llm"
        },
        "invoice_date": {
          "value": "2024-01-15",
          "confidence": 0.92,
          "source": "llm"
        },
        "total_amount": {
          "value": "5000.00",
          "confidence": 0.98,
          "source": "llm"
        },
        "vendor_name": {
          "value": "ABC Corporation",
          "confidence": 0.88,
          "source": "llm"
        }
      },
      "validation": {
        "valid": false,
        "errors": [
          {
            "field": "invoice_number",
            "message": "Invoice number format is invalid"
          }
        ],
        "warnings": [
          {
            "field": "vendor_name",
            "message": "Vendor name confidence is below 90%"
          }
        ]
      },
      "pii": {
        "masked": true,
        "tokens_created": 5,
        "kinds": ["EMAIL", "PHONE_NUMBER", "PERSON_NAME"]
      }
    }
  ]
}
```

**Response (400):**
```json
{
  "error": "Upload at least one invoice file using the 'files' field."
}
```

---

### 3. Upload Invoices (Batch - Asynchronous)

**Endpoint:** `POST /api/invoices/batch`

**Description:** Upload multiple invoice files for asynchronous batch processing. Processing happens in the background, and you can check status using the job_id.

**Request Headers:**
- `Content-Type: multipart/form-data`

**Request Payload:**
- Form parameter: `files` (or `file`) - Multiple PDF/image files

**Response (202):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "total_files": 5
}
```

**Response (400):**
```json
{
  "error": "Upload at least one invoice file using the 'files' field."
}
```

---

### 4. Get Batch Job Status

**Endpoint:** `GET /api/invoices/batch/{job_id}`

**Description:** Check the status and progress of a batch processing job.

**Path Parameters:**
- `job_id` (string, required) - UUID of the batch job

**Request:** No payload required.

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:45Z",
  "total": 5,
  "completed": 3,
  "results": [
    {
      "id": "uuid-1",
      "original_filename": "invoice_001.pdf",
      "status": "completed",
      "extraction": {...}
    },
    {
      "id": "uuid-2",
      "original_filename": "invoice_002.pdf",
      "status": "completed",
      "extraction": {...}
    },
    {
      "id": "uuid-3",
      "original_filename": "invoice_003.pdf",
      "status": "completed",
      "extraction": {...}
    }
  ]
}
```

**Response (404):**
```json
{
  "error": "Batch job not found."
}
```

---

### 5. List All Invoices

**Endpoint:** `GET /api/invoices`

**Description:** Get a list of all processed invoices with overall confidence scores.

**Request:** No payload required.

**Response (200):**
```json
{
  "invoices": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "original_filename": "invoice_001.pdf",
      "status": "completed",
      "file_size": 245632,
      "content_type": "application/pdf",
      "overall_confidence": 85,
      "confidence_level": "High",
      "extraction": {...},
      "validation": {...}
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "original_filename": "invoice_002.pdf",
      "status": "needs_review",
      "file_size": 198752,
      "content_type": "image/png",
      "overall_confidence": 65,
      "confidence_level": "Medium",
      "extraction": {...},
      "validation": {...}
    }
  ],
  "count": 10
}
```

---

### 6. Get Invoice Details

**Endpoint:** `GET /api/invoices/{invoice_id}`

**Description:** Get detailed information for a specific invoice including extraction, validation, and metadata.

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "stored_filename": "550e8400-e29b-41d4-a716-446655440000-invoice_001.pdf",
  "status": "completed",
  "upload_path": "/path/to/upload/file",
  "ocr_text_path": "/path/to/ocr/text",
  "masked_text_path": "/path/to/masked/text",
  "pii_map_path": "/path/to/pii/map",
  "file_size": 245632,
  "content_type": "application/pdf",
  "extraction": {
    "invoice_number": {"value": "INV-2024-001", "confidence": 0.95, "source": "llm"},
    "invoice_date": {"value": "2024-01-15", "confidence": 0.92, "source": "llm"},
    "total_amount": {"value": "5000.00", "confidence": 0.98, "source": "llm"}
  },
  "validation": {
    "valid": true,
    "errors": [
      {
        "field": "vendor_name",
        "message": "Vendor name is missing or empty"
      },
      {
        "field": "invoice_date",
        "message": "Invoice date format is invalid"
      }
    ],
    "warnings": [
      {
        "field": "total_amount",
        "message": "Amount precision exceeds expected decimal places"
      }
    ]
  }
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

### 7. Download Invoice File

**Endpoint:** `GET /api/invoices/{invoice_id}/file`

**Description:** Download the original invoice file (PDF or image).

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):** Binary file download with appropriate `Content-Type` header.

**Response (404):**
```json
{
  "error": "Invoice file not found."
}
```

---

### 8. Review Invoice (Correct Fields)

**Endpoint:** `PATCH /api/invoices/{invoice_id}/review`

**Description:** Review and correct extracted fields for an invoice. Updates extraction with human-reviewed values (confidence set to 1.0).

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request Headers:**
- `Content-Type: application/json`

**Request Payload:**
```json
{
  "fields": {
    "invoice_number": "INV-2024-CORRECTED-001",
    "total_amount": "5250.00",
    "vendor_name": "ABC Corporation Ltd"
  }
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "status": "completed",
  "extraction": {
    "invoice_number": {
      "value": "INV-2024-CORRECTED-001",
      "confidence": 1.0,
      "source": "reviewer"
    },
    "total_amount": {
      "value": "5250.00",
      "confidence": 1.0,
      "source": "reviewer"
    },
    "vendor_name": {
      "value": "ABC Corporation Ltd",
      "confidence": 1.0,
      "source": "reviewer"
    }
  },
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [
      {
        "field": "total_amount",
        "message": "Updated amount differs from extracted value by 5%"
      }
    ]
  }
}
```

**Response (400):**
```json
{
  "error": "'fields' must be an object."
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

### 9. Get Invoice Overall Confidence Score

**Endpoint:** `GET /api/invoices/{invoice_id}/overall-confidence`

**Description:** Get the overall confidence score for an invoice (0-100).

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):**
```json
{
  "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "overall_confidence": 85,
  "status": "completed"
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

### 10. Get Field Confidence Analysis

**Endpoint:** `GET /api/invoices/{invoice_id}/confidence`

**Description:** Get detailed extraction field confidence analysis.

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):**
```json
{
  "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "confidence_analysis": {
    "fields": [
      {
        "field": "invoice_number",
        "confidence": 0.95,
        "level": "High"
      },
      {
        "field": "invoice_date",
        "confidence": 0.92,
        "level": "High"
      },
      {
        "field": "total_amount",
        "confidence": 0.98,
        "level": "High"
      },
      {
        "field": "vendor_name",
        "confidence": 0.75,
        "level": "Medium"
      }
    ],
    "summary": {
      "average_confidence": 0.90,
      "high_confidence": 3,
      "medium_confidence": 1,
      "low_confidence": 0,
      "total_fields": 4
    }
  }
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

### 11. Get HTML Confidence Report

**Endpoint:** `GET /api/invoices/{invoice_id}/confidence/report`

**Description:** Get an HTML confidence report for visual inspection.

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):**
```json
{
  "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "html_report": "<html>...</html>"
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

### 12. Get OCR Confidence Analysis

**Endpoint:** `GET /api/invoices/{invoice_id}/ocr/confidence`

**Description:** Get OCR text with token-level confidence scores.

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):**
```json
{
  "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "ocr": {
    "fields": [...],
    "summary": {...}
  }
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

### 13. Get OCR Confidence Report

**Endpoint:** `GET /api/invoices/{invoice_id}/ocr/confidence/report`

**Description:** Get comprehensive OCR confidence analysis report.

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):**
```json
{
  "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "report": {
    "fields": [...],
    "summary": {...}
  }
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

### 14. Get OCR Confidence with Highlighting

**Endpoint:** `GET /api/invoices/{invoice_id}/ocr/confidence/highlighted`

**Description:** Get OCR text as HTML with low-confidence tokens highlighted.

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):**
```json
{
  "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "html": "<html>...</html>",
  "statistics": {
    "average_confidence": 0.90,
    "high_confidence": 3,
    "medium_confidence": 1,
    "low_confidence": 0,
    "total_fields": 4
  },
  "warnings": []
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

### 15. Get UI Confidence Visualization

**Endpoint:** `GET /api/invoices/{invoice_id}/confidence/ui`

**Description:** Get comprehensive UI confidence visualization combining OCR and extraction confidence.

**Path Parameters:**
- `invoice_id` (string, required) - UUID of the invoice

**Request:** No payload required.

**Response (200):**
```json
{
  "invoice_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice_001.pdf",
  "validation": {
    "valid": true,
    "errors": [
      {
        "field": "vendor_name",
        "message": "Vendor name is missing or empty"
      }
    ],
    "warnings": [
      {
        "field": "total_amount",
        "message": "Amount precision exceeds expected decimal places"
      }
    ]
  },
  "widget_data": {
    "fields": [
      {
        "field": "invoice_number",
        "confidence": 0.95,
        "level": "High"
      },
      {
        "field": "total_amount",
        "confidence": 0.98,
        "level": "High"
      }
    ],
    "summary": {
      "average_confidence": 0.90,
      "high_confidence": 3,
      "medium_confidence": 1,
      "low_confidence": 0,
      "total_fields": 4
    },
    "html_report": "<html>...</html>",
    "ui_hints": {
      "color_scheme": {
        "high": "#4CAF50",
        "medium": "#FFC107",
        "low": "#F44336"
      },
      "show_confidence_percentages": true,
      "enable_manual_override": true
    }
  }
}
```

**Response (404):**
```json
{
  "error": "Invoice not found."
}
```

---

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request:**
```json
{
  "error": "Description of the validation error"
}
```

**404 Not Found:**
```json
{
  "error": "Invoice not found."
}
```

---

## Common Field Definitions

### Extraction Object
```json
{
  "field_name": {
    "value": "extracted_value",
    "confidence": 0.95,
    "source": "llm|ocr|reviewer"
  }
}
```

### Validation Object
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "field": "field_name",
      "message": "Warning message"
    }
  ]
}
```

### Confidence Levels
- **High**: 80-100%
- **Medium**: 50-79%
- **Low**: 0-49%

---

## Usage Examples

### Example 1: Upload and Process an Invoice
```bash
curl -X POST http://localhost:5000/api/invoices \
  -F "files=@invoice.pdf"
```

### Example 2: Get Invoice Details
```bash
curl http://localhost:5000/api/invoices/550e8400-e29b-41d4-a716-446655440000
```

### Example 3: Review and Correct Fields
```bash
curl -X PATCH http://localhost:5000/api/invoices/550e8400-e29b-41d4-a716-446655440000/review \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "invoice_number": "INV-2024-CORRECTED",
      "total_amount": "5250.00"
    }
  }'
```

### Example 4: Batch Upload
```bash
curl -X POST http://localhost:5000/api/invoices/batch \
  -F "files=@invoice1.pdf" \
  -F "files=@invoice2.pdf" \
  -F "files=@invoice3.pdf"
```

### Example 5: Check Batch Status
```bash
curl http://localhost:5000/api/invoices/batch/550e8400-e29b-41d4-a716-446655440000
```

---

## Notes

- All invoice IDs are UUIDs.
- Confidence scores are decimal values between 0.0 and 1.0.
- PII (Personally Identifiable Information) is automatically masked for privacy.
- The `source` field indicates where the data came from: `llm` (LLM extraction), `ocr` (OCR extraction), or `reviewer` (human review).
- Batch processing jobs return immediately with a job_id; use the status endpoint to monitor progress.
