import json
import os

from app.services.extractor import InvoiceExtractor
from app.services.pii_masker import PiiMasker


class LlmPayloadRejected(Exception):
    pass


class LlmConfigurationError(Exception):
    pass


class LlmExtractionError(Exception):
    pass


INVOICE_EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "vendor": {"type": ["string", "null"]},
        "invoice_number": {"type": ["string", "null"]},
        "invoice_date": {
            "type": ["string", "null"],
            "description": "Invoice date in YYYY-MM-DD format when available.",
        },
        "due_date": {
            "type": ["string", "null"],
            "description": "Due date in YYYY-MM-DD format when available.",
        },
        "currency": {"type": ["string", "null"]},
        "total_amount": {"type": ["number", "null"]},
        "tax_id_token": {
            "type": ["string", "null"],
            "description": "Masked tax identifier token such as [GSTIN_1], never the original tax id.",
        },
        "field_confidences": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "vendor": {"type": "number"},
                "invoice_number": {"type": "number"},
                "invoice_date": {"type": "number"},
                "due_date": {"type": "number"},
                "currency": {"type": "number"},
                "total_amount": {"type": "number"},
                "tax_id_token": {"type": "number"},
            },
            "required": [
                "vendor",
                "invoice_number",
                "invoice_date",
                "due_date",
                "currency",
                "total_amount",
                "tax_id_token",
            ],
        },
    },
    "required": [
        "vendor",
        "invoice_number",
        "invoice_date",
        "due_date",
        "currency",
        "total_amount",
        "tax_id_token",
        "field_confidences",
    ],
}


class InvoiceLlmClient:
    """LLM boundary. Only masked text is accepted by this service."""

    def __init__(
        self,
        provider="local",
        masker=None,
        model=None,
        openai_client=None,
        langchain_client=None,
        base_url=None,
        verify_ssl=None,
    ):
        self.provider = provider
        self.masker = masker or PiiMasker()
        self.local_extractor = InvoiceExtractor()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.openai_client = openai_client
        self.langchain_client = langchain_client
        self.base_url = base_url or os.getenv("GENAILAB_BASE_URL", "https://genailab.tcs.in")
        self.verify_ssl = verify_ssl

    def extract_invoice(self, masked_text):
        try:
            self.masker.assert_masked_for_llm(masked_text)
        except ValueError as exc:
            raise LlmPayloadRejected(str(exc)) from exc

        if self.provider == "openai":
            return self._openai_extract(masked_text)

        if self.provider == "genailab":
            return self._genailab_extract(masked_text)

        if self.provider != "local":
            raise LlmConfigurationError(f"Unsupported LLM provider: {self.provider}")

        return self.local_extractor.extract(masked_text)

    def _openai_extract(self, masked_text):
        client = self.openai_client or self._create_openai_client()
        try:
            response = client.responses.create(
                model=self.model,
                instructions=(
                    "Extract invoice fields from masked OCR text. "
                    "Use only the supplied masked text. Never infer or recreate masked PII. "
                    "Return null for missing values."
                ),
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": masked_text,
                            }
                        ],
                    }
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "invoice_extraction",
                        "strict": True,
                        "schema": INVOICE_EXTRACTION_SCHEMA,
                    }
                },
            )
        except Exception as exc:
            raise LlmExtractionError(f"OpenAI extraction failed: {exc}") from exc

        payload = self._parse_response_json(response)
        return self._normalize_openai_payload(payload)

    def _create_openai_client(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise LlmConfigurationError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LlmConfigurationError("Install the openai package to use LLM_PROVIDER=openai.") from exc
        return OpenAI()

    def _genailab_extract(self, masked_text):
        llm = self.langchain_client or self._create_genailab_client()
        try:
            response = llm.invoke(self._genailab_prompt(masked_text))
        except Exception as exc:
            raise LlmExtractionError(f"GenAI Lab extraction failed: {exc}") from exc

        payload = self._parse_response_json(response)
        return self._normalize_openai_payload(payload, source="masked_text_genailab")

    def _create_genailab_client(self):
        api_key = os.getenv("GENAILAB_API_KEY")
        if not api_key:
            raise LlmConfigurationError("GENAILAB_API_KEY is required when LLM_PROVIDER=genailab.")
        try:
            import httpx
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise LlmConfigurationError(
                "Install httpx and langchain-openai to use LLM_PROVIDER=genailab."
            ) from exc

        verify_ssl = self.verify_ssl
        if verify_ssl is None:
            verify_ssl = os.getenv("GENAILAB_VERIFY_SSL", "false").lower() == "true"

        http_client = httpx.Client(verify=verify_ssl)
        return ChatOpenAI(
            base_url=self.base_url,
            model=os.getenv("GENAILAB_MODEL", self.model),
            api_key=api_key,
            http_client=http_client,
        )

    def _genailab_prompt(self, masked_text):
        return (
            "Extract invoice fields from the masked OCR text below.\n"
            "Privacy rule: use only the supplied masked text. Never infer, recover, or output original PII. "
            "Masked tokens such as [GSTIN_1], [EMAIL_1], and [CONTACT_LINE_1] must remain masked.\n"
            "Return only valid JSON with these keys: vendor, invoice_number, invoice_date, due_date, "
            "currency, total_amount, tax_id_token, field_confidences.\n"
            "Dates must be YYYY-MM-DD when available. Missing values must be null. "
            "field_confidences must contain numeric 0 to 1 scores for every field.\n\n"
            f"Masked OCR text:\n{masked_text}"
        )

    def _parse_response_json(self, response):
        output_text = getattr(response, "output_text", None)
        if output_text is None:
            output_text = getattr(response, "content", None)
        if not output_text:
            output_text = self._extract_text_from_response(response)
        output_text = self._strip_json_fence(output_text)
        try:
            return json.loads(output_text)
        except (TypeError, json.JSONDecodeError) as exc:
            raise LlmExtractionError("OpenAI response did not contain valid JSON.") from exc

    def _extract_text_from_response(self, response):
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    return text
        return ""

    def _strip_json_fence(self, text):
        if not isinstance(text, str):
            return text
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def _normalize_openai_payload(self, payload, source="masked_text_openai"):
        confidences = payload.get("field_confidences") or {}
        extraction = {"source": source}
        fields = (
            "vendor",
            "invoice_number",
            "invoice_date",
            "due_date",
            "currency",
            "total_amount",
            "tax_id_token",
        )

        for field in fields:
            value = payload.get(field)
            if value is None or value == "":
                continue
            normalized = {
                "value": value,
                "confidence": self._confidence(confidences.get(field)),
            }
            if field.endswith("_date"):
                normalized["normalized"] = value
            extraction[field] = normalized

        return extraction

    def _confidence(self, value):
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.7
        return max(0.0, min(confidence, 1.0))
