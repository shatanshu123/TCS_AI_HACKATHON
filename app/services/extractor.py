import re
from datetime import datetime


class InvoiceExtractor:
    """Deterministic fallback extractor that runs on already-masked text."""

    DATE_VALUE = re.compile(
        r"(?i)\b("
        r"[0-3]?\d[/-][01]?\d[/-]\d{2,4}"
        r"|\d{4}-[01]\d-[0-3]\d"
        r"|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+[0-3]?\d,?\s+\d{4}"
        r")"
    )
    MONEY = re.compile(
        r"(?i)\b(?:grand\s+total|total\s+amount|amount\s+due|invoice\s+total|balance\s+due|total)\b"
        r"[^\dA-Z$-]{0,20}(?:INR|Rs\.?|USD|\$)?\s*([0-9][0-9,]*(?:\.\d{1,2})?)"
    )
    INVOICE_NUMBER = re.compile(
        r"(?i)\b(?:invoice\s*(?:no|number|#)|inv\s*(?:no|#))\b\s*[:#-]?\s*([A-Z0-9][A-Z0-9/-]{1,40})"
    )
    STANDALONE_INVOICE_NUMBER = re.compile(r"(?i)\bINV[-/][A-Z0-9][A-Z0-9/-]{2,40}\b")
    AMOUNTISH = re.compile(r"(?:INR|Rs\.?|USD|\$)\s*[0-9][0-9,]*(?:\.\d{1,2})?", re.I)

    def extract(self, masked_text):
        lines = [line.strip() for line in masked_text.splitlines() if line.strip()]

        extraction = {
            "vendor": self._extract_vendor(lines),
            "invoice_number": self._extract_invoice_number(masked_text, lines),
            "invoice_date": self._extract_date(lines, "invoice_date"),
            "due_date": self._extract_date(lines, "due_date"),
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
        from_vendor = self._extract_vendor_after_label(lines)
        if from_vendor:
            return from_vendor

        ignored = (
            "invoice",
            "tax invoice",
            "bill to",
            "ship to",
            "from",
            "date",
            "total",
            "subtotal",
            "tax",
            "gstin",
            "pan",
        )
        for line in lines[:10]:
            normalized = line.lower().strip(": ")
            if len(normalized) < 3:
                continue
            if any(normalized.startswith(term) for term in ignored):
                continue
            if not self._is_business_name_candidate(line):
                continue
            return {"value": line[:120], "confidence": 0.58}
        return None

    def _extract_vendor_after_label(self, lines):
        for index, line in enumerate(lines):
            if line.lower().strip(": ") != "from":
                continue
            for candidate in lines[index + 1:index + 5]:
                if self._is_business_name_candidate(candidate):
                    return {"value": candidate[:120], "confidence": 0.82}
        return None

    def _is_business_name_candidate(self, line):
        normalized = line.lower().strip(": ")
        if not normalized or normalized.startswith("["):
            return False
        if normalized in {"bill to", "invoice", "tax invoice", "from"}:
            return False
        if self.AMOUNTISH.search(line):
            return False
        return True

    def _extract_invoice_number(self, text, lines):
        match = self.INVOICE_NUMBER.search(text)
        if match:
            return {"value": match.group(1), "confidence": 0.82}

        for line in reversed(lines):
            match = self.STANDALONE_INVOICE_NUMBER.search(line)
            if match:
                return {"value": match.group(0), "confidence": 0.74}
        return None

    def _extract_date(self, lines, field):
        for index, line in enumerate(lines):
            if not self._is_date_label(line, field):
                continue

            value = self._first_date_value(self._text_after_date_label(line, field))
            if value is None and index + 1 < len(lines):
                value = self._first_date_value(lines[index + 1])
            if value is None:
                continue
            return {"value": value, "normalized": self._normalize_date(value), "confidence": 0.78}
        return None

    def _is_date_label(self, line, field):
        normalized = line.lower()
        if field == "invoice_date":
            if "due date" in normalized or "payment due" in normalized:
                return False
            invoice_labels = ("invoice date", "date issued", "issue date")
            return any(label in normalized for label in invoice_labels) or normalized.strip(": ") == "date"
        return "due date" in normalized or "payment due" in normalized

    def _text_after_date_label(self, line, field):
        labels = (
            ("invoice date", "date issued", "issue date", "date")
            if field == "invoice_date"
            else ("payment due", "due date")
        )
        lowered = line.lower()
        positions = [lowered.find(label) + len(label) for label in labels if lowered.find(label) >= 0]
        if not positions:
            return ""
        return line[min(positions):]

    def _first_date_value(self, text):
        match = self.DATE_VALUE.search(text)
        if not match:
            return None
        return match.group(1)

    def _extract_total(self, text):
        matches = self.MONEY.findall(text)
        if not matches:
            return None
        values = [float(match.replace(",", "")) for match in matches]
        return {"value": max(values), "confidence": 0.72}

    def _extract_currency(self, text):
        if re.search(r"\b(?:INR|Rs\.?)\b", text, re.I):
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
        formats = (
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d/%m/%y",
            "%d-%m-%y",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%B %d %Y",
            "%b %d %Y",
        )
        for date_format in formats:
            try:
                return datetime.strptime(value, date_format).date().isoformat()
            except ValueError:
                continue
        return None
