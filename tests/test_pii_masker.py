import pytest

from app.services.pii_masker import PiiMasker


def test_masks_sensitive_invoice_data_before_llm():
    text = """
    Tax Invoice
    Vendor GSTIN: 29ABCDE1234F1Z5
    Contact Person: Anita Sharma, +91 9876543210, anita@example.com
    PAN: ABCDE1234F
    Account Number: 123456789012
    IFSC: HDFC0001234
    UPI: vendor@okaxis
    Bill To: Raj Kumar, 21 Street Road, Bengaluru 560001
    Total Amount: INR 12,300.50
    """

    result = PiiMasker().mask(text)

    assert "anita@example.com" not in result.masked_text
    assert "9876543210" not in result.masked_text
    assert "29ABCDE1234F1Z5" not in result.masked_text
    assert "ABCDE1234F" not in result.masked_text
    assert "123456789012" not in result.masked_text
    assert "HDFC0001234" not in result.masked_text
    assert "vendor@okaxis" not in result.masked_text
    assert "Anita Sharma" not in result.masked_text
    assert "[CONTACT_LINE_1]" in result.masked_text
    assert "[GSTIN_1]" in result.masked_text
    assert "[BANK_ACCOUNT_1]" in result.masked_text


def test_rejects_unmasked_payload_for_llm():
    with pytest.raises(ValueError):
        PiiMasker().assert_masked_for_llm("Email finance@example.com Total INR 20")


def test_allows_masked_payload_for_llm():
    PiiMasker().assert_masked_for_llm("Email [EMAIL_1] Total INR 20")


def test_masks_unlabeled_address_lines():
    text = """
    FROM
    Creative Solutions LLC
    123 Business Avenue, Suite 100
    San Francisco, CA 94105
    BILL TO
    Global Tech Industries
    789 Innovation Drive
    Seattle, WA 98101
    """

    result = PiiMasker().mask(text)

    assert "123 Business Avenue" not in result.masked_text
    assert "San Francisco" not in result.masked_text
    assert "789 Innovation Drive" not in result.masked_text
    assert "Seattle" not in result.masked_text
    assert "[ADDRESS_LINE_1]" in result.masked_text
