import io

from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True
    STORAGE_DIR = Config.BASE_DIR / "storage-test"
    UPLOAD_DIR = STORAGE_DIR / "uploads"
    TEXT_DIR = STORAGE_DIR / "texts"
    MASK_DIR = STORAGE_DIR / "masked"
    DATABASE_PATH = STORAGE_DIR / "invoices.sqlite3"


def test_upload_text_invoice_masks_pii_and_extracts_fields():
    app = create_app(TestConfig)
    client = app.test_client()
    invoice_text = b"""
    Acme Office Supplies Pvt Ltd
    Tax Invoice
    Invoice No: INV-2025-001
    Invoice Date: 20/04/2026
    Vendor GSTIN: 29ABCDE1234F1Z5
    Contact Person: Anita Sharma +91 9876543210 anita@example.com
    Total Amount: INR 12,300.50
    """

    response = client.post(
        "/api/invoices",
        data={"files": (io.BytesIO(invoice_text), "invoice.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    payload = response.get_json()
    invoice = payload["invoices"][0]
    assert invoice["pii"]["masked"] is True
    assert invoice["extraction"]["invoice_number"]["value"] == "INV-2025-001"
    assert invoice["extraction"]["total_amount"]["value"] == 12300.50
    assert invoice["validation"]["valid"] is True

