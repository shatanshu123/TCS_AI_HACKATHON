import json

import pytest

from app.services.llm_client import InvoiceLlmClient, LlmPayloadRejected


class FakeResponses:
    def __init__(self):
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        return FakeResponse(
            {
                "vendor": "Acme Office Supplies Pvt Ltd",
                "invoice_number": "INV-2025-001",
                "invoice_date": "2026-04-20",
                "due_date": None,
                "currency": "INR",
                "total_amount": 12300.5,
                "tax_id_token": "[GSTIN_1]",
                "field_confidences": {
                    "vendor": 0.9,
                    "invoice_number": 0.95,
                    "invoice_date": 0.9,
                    "due_date": 0,
                    "currency": 0.8,
                    "total_amount": 0.92,
                    "tax_id_token": 0.99,
                },
            }
        )


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponses()


class FakeResponse:
    def __init__(self, payload):
        self.output_text = json.dumps(payload)


class FakeLangChainResponse:
    def __init__(self, payload):
        self.content = f"```json\n{json.dumps(payload)}\n```"


class FakeLangChainClient:
    def __init__(self):
        self.prompt = None

    def invoke(self, prompt):
        self.prompt = prompt
        return FakeLangChainResponse(
            {
                "vendor": "Acme Office Supplies Pvt Ltd",
                "invoice_number": "INV-2025-001",
                "invoice_date": "2026-04-20",
                "due_date": None,
                "currency": "INR",
                "total_amount": 12300.5,
                "tax_id_token": "[GSTIN_1]",
                "field_confidences": {
                    "vendor": 0.9,
                    "invoice_number": 0.95,
                    "invoice_date": 0.9,
                    "due_date": 0,
                    "currency": 0.8,
                    "total_amount": 0.92,
                    "tax_id_token": 0.99,
                },
            }
        )


def test_openai_provider_sends_only_masked_text_and_normalizes_response():
    fake_client = FakeOpenAIClient()
    client = InvoiceLlmClient(
        provider="openai",
        openai_client=fake_client,
        model="test-model",
    )

    extraction = client.extract_invoice(
        "Vendor Acme Office Supplies Pvt Ltd\n"
        "Invoice No: INV-2025-001\n"
        "Vendor GSTIN: [GSTIN_1]\n"
        "Contact: [CONTACT_LINE_1]\n"
        "Total Amount: INR 12,300.50"
    )

    request = fake_client.responses.request
    sent_text = request["input"][0]["content"][0]["text"]
    assert "anita@example.com" not in sent_text
    assert request["model"] == "test-model"
    assert request["text"]["format"]["type"] == "json_schema"
    assert extraction["source"] == "masked_text_openai"
    assert extraction["invoice_number"]["value"] == "INV-2025-001"
    assert extraction["tax_id_token"]["value"] == "[GSTIN_1]"


def test_openai_provider_rejects_raw_pii_before_api_call():
    fake_client = FakeOpenAIClient()
    client = InvoiceLlmClient(provider="openai", openai_client=fake_client)

    with pytest.raises(LlmPayloadRejected):
        client.extract_invoice("Contact finance@example.com Total INR 20")

    assert fake_client.responses.request is None


def test_genailab_provider_uses_langchain_client_with_masked_prompt():
    fake_client = FakeLangChainClient()
    client = InvoiceLlmClient(provider="genailab", langchain_client=fake_client)

    extraction = client.extract_invoice(
        "Vendor Acme Office Supplies Pvt Ltd\n"
        "Invoice No: INV-2025-001\n"
        "Vendor GSTIN: [GSTIN_1]\n"
        "Contact: [CONTACT_LINE_1]\n"
        "Total Amount: INR 12,300.50"
    )

    assert "Masked OCR text:" in fake_client.prompt
    assert "anita@example.com" not in fake_client.prompt
    assert "9876543210" not in fake_client.prompt
    assert extraction["source"] == "masked_text_genailab"
    assert extraction["invoice_number"]["value"] == "INV-2025-001"
    assert extraction["tax_id_token"]["value"] == "[GSTIN_1]"
