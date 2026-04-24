from pathlib import Path

from app.services.validator import InvoiceValidator


def test_validation_rejects_unannotated_required_fields():
    validator = InvoiceValidator()
    validation = validator.validate(
        {
            "vendor": "Example Corp",
            "invoice_number": "INV-2026-100",
            "invoice_date": {"value": "2026-04-24", "normalized": "2026-04-24", "confidence": 0.95},
            "total_amount": {"value": 2500.0, "confidence": 0.95},
        },
        {},
    )

    assert validation["valid"] is False
    assert any(error["field"] == "vendor" for error in validation["errors"])
    assert any(error["field"] == "invoice_number" for error in validation["errors"])
    assert any(
        "annotated with value and confidence" in error["message"]
        for error in validation["errors"]
    )


def test_validation_accepts_annotated_required_fields():
    validator = InvoiceValidator()
    validation = validator.validate(
        {
            "vendor": {"value": "Example Corp", "confidence": 0.95},
            "invoice_number": {"value": "INV-2026-100", "confidence": 0.88},
            "invoice_date": {"value": "24/04/2026", "normalized": "2026-04-24", "confidence": 0.90},
            "total_amount": {"value": 2500.0, "confidence": 0.95},
        },
        {},
    )

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_sample_dataset_is_documented_as_synthetic():
    sample_readme = Path(__file__).resolve().parents[1] / "sample-dataset" / "README.md"
    content = sample_readme.read_text(encoding="utf-8")

    assert "Synthetic test data" in content
