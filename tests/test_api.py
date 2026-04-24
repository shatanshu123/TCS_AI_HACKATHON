import time
from pathlib import Path

from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True
    STORAGE_DIR = Config.BASE_DIR / "storage-test"
    UPLOAD_DIR = STORAGE_DIR / "uploads"
    TEXT_DIR = STORAGE_DIR / "texts"
    MASK_DIR = STORAGE_DIR / "masked"
    DATABASE_PATH = STORAGE_DIR / "invoices.sqlite3"


def test_upload_pdf_invoice_masks_pii_and_extracts_fields():
    app = create_app(TestConfig)
    client = app.test_client()
    sample_pdf = Config.BASE_DIR / "sample-dataset" / "invoices" / "invoice-001-standard.pdf"

    with sample_pdf.open("rb") as invoice_file:
        response = client.post(
            "/api/invoices",
            data={"files": (invoice_file, "invoice-001-standard.pdf")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 201
    payload = response.get_json()
    invoice = payload["invoices"][0]
    assert invoice["pii"]["masked"] is True
    assert invoice["database_storage"]["invoice_blob_stored"] is True
    assert invoice["database_storage"]["content_type"] == "application/pdf"
    assert invoice["database_storage"]["file_size"] == sample_pdf.stat().st_size
    assert invoice["extraction"]["invoice_number"]["value"] == "INV-2026-001"
    assert invoice["extraction"]["total_amount"]["value"] == 14160.00
    assert invoice["validation"]["valid"] is True

    file_response = client.get(f"/api/invoices/{invoice['id']}/file")
    assert file_response.status_code == 200
    assert file_response.mimetype == "application/pdf"
    assert file_response.data == sample_pdf.read_bytes()


def test_rejects_text_invoice_uploads():
    app = create_app(TestConfig)
    client = app.test_client()

    with Path(__file__).open("rb") as invoice_file:
        response = client.post(
            "/api/invoices",
            data={"files": (invoice_file, "invoice.txt")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 201
    invoice = response.get_json()["invoices"][0]
    assert invoice["status"] == "rejected"
    assert "Unsupported file type" in invoice["error"]


def test_missing_total_pdf_needs_review():
    app = create_app(TestConfig)
    client = app.test_client()
    sample_pdf = Config.BASE_DIR / "sample-dataset" / "invoices" / "invoice-002-missing-total.pdf"

    with sample_pdf.open("rb") as invoice_file:
        response = client.post(
            "/api/invoices",
            data={"files": (invoice_file, "invoice-002-missing-total.pdf")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 201
    invoice = response.get_json()["invoices"][0]
    assert invoice["status"] == "needs_review"
    assert any(error["field"] == "total_amount" for error in invoice["validation"]["errors"])


def test_batch_invoice_uploads_in_background():
    app = create_app(TestConfig)
    client = app.test_client()
    sample_pdf = Config.BASE_DIR / "sample-dataset" / "invoices" / "invoice-001-standard.pdf"

    with sample_pdf.open("rb") as invoice_file:
        response = client.post(
            "/api/invoices/batch",
            data={"files": (invoice_file, "invoice-001-standard.pdf")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload["status"] == "queued"
    assert payload["total_files"] == 1
    job_id = payload["job_id"]

    status = None
    for _ in range(30):
        status_response = client.get(f"/api/invoices/batch/{job_id}")
        assert status_response.status_code == 200
        status = status_response.get_json()
        if status["status"] == "finished":
            break
        time.sleep(0.1)

    assert status is not None
    assert status["status"] == "finished"
    assert status["completed"] == 1
    assert len(status["results"]) == 1
    assert status["results"][0]["status"] == "completed"
