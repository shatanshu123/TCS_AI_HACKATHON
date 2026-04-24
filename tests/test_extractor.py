from app.services.extractor import InvoiceExtractor
from app.services.pii_masker import PiiMasker


def test_extracts_fields_from_split_label_pdf_text_layout():
    text = """
Subtotal $12,125.00
Tax (8.5%) $1,030.63
Total $13,155.63INVOICE
FROM
Creative Solutions LLC
123 Business Avenue, Suite 100
San Francisco, CA 94105
hello@example.com BILL TO
Global Tech Industries
789 Innovation Drive
Seattle, WA 98101
ap@example.com
DATE ISSUED
April 24, 2026DUE DATE
May 08, 2026AMOUNT DUE
$13,155.63
INV-2026-0401
"""

    masked = PiiMasker().mask(text).masked_text
    extraction = InvoiceExtractor().extract(masked)

    assert "123 Business Avenue" not in masked
    assert "San Francisco" not in masked
    assert extraction["vendor"]["value"] == "Creative Solutions LLC"
    assert extraction["invoice_number"]["value"] == "INV-2026-0401"
    assert extraction["invoice_date"]["normalized"] == "2026-04-24"
    assert extraction["due_date"]["normalized"] == "2026-05-08"
    assert extraction["currency"]["value"] == "USD"
    assert extraction["total_amount"]["value"] == 13155.63

