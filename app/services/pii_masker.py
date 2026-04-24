import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PiiFinding:
    kind: str
    start: int
    end: int
    value: str


@dataclass(frozen=True)
class MaskingResult:
    masked_text: str
    pii_map: dict
    findings: list[PiiFinding]


class PiiMasker:
    """Masks personal and sensitive invoice data before LLM processing."""

    GSTIN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b", re.I)
    PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.I)
    EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
    UPI = re.compile(r"\b[\w.-]{2,}@[A-Z]{2,}\b", re.I)
    IFSC = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.I)
    AADHAAR = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")
    PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{2}[\s-]?\d{3}[\s-]?\d{4}(?!\d)")
    CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
    BANK_ACCOUNT_CONTEXT = re.compile(
        r"(?i)\b(?:a/c|acct|account|bank account|beneficiary account)\b[^\n\d]{0,30}(\d{9,18})"
    )
    CONTACT_LINE = re.compile(
        r"(?im)^\s*(?:contact person|attention|attn|prepared for|bill to|ship to|deliver to|customer)\s*:.*$"
    )
    ADDRESS_LINE = re.compile(
        r"(?im)^.*\b(?:address|street|st\.|road|rd\.|lane|sector|phase|floor|tower|pin|pincode|zip)\b.*$"
    )
    MASK_TOKEN = re.compile(r"\[[A-Z_]+_\d+\]")

    def mask(self, text):
        if not text:
            return MaskingResult(masked_text="", pii_map={}, findings=[])

        findings = self.find(text)
        selected = self._select_non_overlapping(findings)
        counters = {}
        pii_map = {}
        parts = []
        cursor = 0

        for finding in selected:
            parts.append(text[cursor:finding.start])
            token = self._token_for(finding, counters)
            parts.append(token)
            pii_map[token] = {
                "kind": finding.kind,
                "sha256": hashlib.sha256(finding.value.encode("utf-8")).hexdigest(),
                "value": finding.value,
            }
            cursor = finding.end

        parts.append(text[cursor:])

        return MaskingResult(
            masked_text="".join(parts),
            pii_map=pii_map,
            findings=selected,
        )

    def find(self, text):
        findings = []

        for match in self.BANK_ACCOUNT_CONTEXT.finditer(text):
            findings.append(PiiFinding("BANK_ACCOUNT", match.start(1), match.end(1), match.group(1)))

        detectors = [
            ("GSTIN", self.GSTIN),
            ("PAN", self.PAN),
            ("EMAIL", self.EMAIL),
            ("UPI", self.UPI),
            ("IFSC", self.IFSC),
            ("AADHAAR", self.AADHAAR),
            ("PHONE", self.PHONE),
            ("CONTACT_LINE", self.CONTACT_LINE),
            ("ADDRESS_LINE", self.ADDRESS_LINE),
        ]

        for kind, pattern in detectors:
            for match in pattern.finditer(text):
                findings.append(PiiFinding(kind, match.start(), match.end(), match.group(0)))

        for match in self.CARD.finditer(text):
            value = match.group(0)
            digits = re.sub(r"\D", "", value)
            if self._luhn_valid(digits):
                findings.append(PiiFinding("CARD", match.start(), match.end(), value))

        return findings

    def assert_masked_for_llm(self, text):
        visible_findings = [
            finding for finding in self.find(text)
            if not self.MASK_TOKEN.fullmatch(finding.value)
        ]
        if visible_findings:
            kinds = sorted({finding.kind for finding in visible_findings})
            raise ValueError(f"LLM payload contains unmasked sensitive data: {', '.join(kinds)}")

    def _select_non_overlapping(self, findings):
        priority = {
            "CONTACT_LINE": 0,
            "ADDRESS_LINE": 0,
            "BANK_ACCOUNT": 1,
            "GSTIN": 1,
            "PAN": 1,
            "IFSC": 1,
            "EMAIL": 2,
            "UPI": 2,
            "PHONE": 2,
            "AADHAAR": 3,
            "CARD": 4,
        }
        ordered = sorted(
            findings,
            key=lambda item: (item.start, priority.get(item.kind, 99), -(item.end - item.start)),
        )
        selected = []
        occupied_until = -1

        for finding in ordered:
            if finding.start < occupied_until:
                continue
            selected.append(finding)
            occupied_until = finding.end

        return selected

    def _token_for(self, finding, counters):
        counters[finding.kind] = counters.get(finding.kind, 0) + 1
        return f"[{finding.kind}_{counters[finding.kind]}]"

    def _luhn_valid(self, digits):
        if len(digits) < 13:
            return False

        total = 0
        reverse_digits = digits[::-1]
        for index, char in enumerate(reverse_digits):
            number = int(char)
            if index % 2 == 1:
                number *= 2
                if number > 9:
                    number -= 9
            total += number

        return total % 10 == 0
