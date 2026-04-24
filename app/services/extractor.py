import re
from datetime import datetime


class InvoiceExtractor:
    """Deterministic fallback extractor that runs on already-masked text."""

    MONEY = re.compile(
        r"(?i)\b(?:grand\s+total|total\s+amount|amount\s+due|invoice\s+total|total)\b"
        r"[^\dA-Z$₹-]{0,20}(?:INR|Rs\.?|USD|\$|₹)?\s*([0-9][0-9,]*(?:\.\d{1,2})?)"
    )
    ANY_MONEY = re.compile(r"(?:INR|Rs\.?|USD|\$|₹)\s*([0-9][0-9,]*(?:\.\d{1,2})?)", re.I)
    INVOICE_NUMBER = re.compile(
        r"(?i)\b(?:invoice\s*(?:no|number|#)|inv\s*(?:no|#))\b\s*[:#-]?\s*([A-Z0-9][A-Z0-9/-]{1,40})"
    )
    DATE_LABELS = {
        "invoice_date": re.compile(
            r"(?i)\b(?:invoice\s*date|date)\b\s*[:#-]?\s*([0-3]?\d[/-][01]?\d[/-]\d{2,4}|\d{4}-[01]\d-[0-3]\d)"
        ),
        "due_date": re.compile(
            r"(?i)\b(?:due\s*date|payment\s*due)\b\s*[:#-]?\s*([0-3]?\d[/-][01]?\d[/-]\d{2,4}|\d{4}-[01]\d-[0-3]\d)"
        ),
    }

    def extract(self, masked_text):
        lines = [line.strip() for line in masked_text.splitlines() if line.strip()]

        extraction = {
            "vendor": self._extract_vendor(lines),
            "invoice_number": self._extract_invoice_number(masked_text),
            "invoice_date": self._extract_date(masked_text, "invoice_date"),
            "due_date": self._extract_date(masked_text, "due_date"),
            "currency": self._extract_currency(masked_text),
            "total_amount": self._extract_total(masked_text),
            "tax_id_token": self._extract_first_token(masked_text, "GSTIN"),
            "source": "masked_text",
        }

        return {
            key: value
            for key, value in extraction.items()
            if value is not None
        }

    def _extract_vendor(self, lines):
        ignored = (
            "invoice",
            "tax invoice",
            "bill to",
            "ship to",
            "date",
            "total",
            "gstin",
            "pan",
        )
        for line in lines[:8]:
            normalized = line.lower().strip(": ")
            if len(normalized) < 3:
                continue
            if any(normalized.startswith(term) for term in ignored):
                continue
            if line.startswith("["):
                continue
            return {"value": line[:120], "confidence": 0.58}
        return None

    def _extract_invoice_number(self, text):
        match = self.INVOICE_NUMBER.search(text)
        if not match:
            return None
        return {"value": match.group(1), "confidence": 0.82}

    def _extract_date(self, text, field):
        match = self.DATE_LABELS[field].search(text)
        if not match:
            return None
        value = match.group(1)
        return {"value": value, "normalized": self._normalize_date(value), "confidence": 0.78}

    def _extract_total(self, text):
        matches = self.MONEY.findall(text)
        if not matches:
            matches = self.ANY_MONEY.findall(text)
        if not matches:
            return None
        values = [float(match.replace(",", "")) for match in matches]
        return {"value": max(values), "confidence": 0.72}

    def _extract_currency(self, text):
        if re.search(r"\b(?:INR|Rs\.?)\b|₹", text, re.I):
            return {"value": "INR", "confidence": 0.8}
        if "$" in text or re.search(r"\bUSD\b", text, re.I):
            return {"value": "USD", "confidence": 0.8}
        return None

    def _extract_first_token(self, text, kind):
        match = re.search(rf"\[{kind}_\d+\]", text)
        if not match:
            return None
        return {"value": match.group(0), "confidence": 0.95}

    def _normalize_date(self, value):
        formats = ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%Y-%m-%d")
        for date_format in formats:
            try:
                return datetime.strptime(value, date_format).date().isoformat()
            except ValueError:
                continue
        return None

