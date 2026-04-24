from datetime import date


class InvoiceValidator:
    REQUIRED_FIELDS = ("vendor", "invoice_number", "invoice_date", "total_amount")

    def validate(self, extraction, pii_map):
        errors = []
        warnings = []

        for field in self.REQUIRED_FIELDS:
            if not extraction.get(field):
                errors.append({"field": field, "message": "Required field is missing."})

        amount = self._field_value(extraction.get("total_amount"))
        if amount is not None and amount <= 0:
            errors.append({"field": "total_amount", "message": "Amount must be greater than zero."})

        invoice_date = self._field_value(extraction.get("invoice_date"), "normalized")
        if invoice_date and invoice_date > date.today().isoformat():
            warnings.append({"field": "invoice_date", "message": "Invoice date is in the future."})

        tax_token = self._field_value(extraction.get("tax_id_token"))
        if tax_token and tax_token not in pii_map:
            warnings.append({"field": "tax_id_token", "message": "Tax token was not found in local PII map."})

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _field_value(self, field, key="value"):
        if isinstance(field, dict):
            return field.get(key)
        return field

