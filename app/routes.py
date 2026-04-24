import json
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from app.services.extractor import InvoiceExtractor
from app.services.llm_client import (
    InvoiceLlmClient,
    LlmConfigurationError,
    LlmExtractionError,
    LlmPayloadRejected,
)
from app.services.ocr import OcrService
from app.services.pii_masker import PiiMasker
from app.services.validator import InvoiceValidator
from app.storage import get_invoice, insert_invoice, list_invoices, update_invoice


api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "invoice-processing-backend"})


@api.post("/api/invoices")
def upload_invoices():
    files = request.files.getlist("files") or request.files.getlist("file")
    if not files:
        return jsonify({"error": "Upload at least one invoice file using the 'files' field."}), 400

    processed = []
    for file_storage in files:
        if not file_storage.filename:
            continue
        processed.append(_process_upload(file_storage))

    return jsonify({"count": len(processed), "invoices": processed}), 201


@api.get("/api/invoices")
def invoices():
    return jsonify({"invoices": list_invoices(current_app.config["DATABASE_PATH"])})


@api.get("/api/invoices/<invoice_id>")
def invoice_detail(invoice_id):
    invoice = get_invoice(current_app.config["DATABASE_PATH"], invoice_id)
    if invoice is None:
        return jsonify({"error": "Invoice not found."}), 404
    return jsonify(invoice)


@api.patch("/api/invoices/<invoice_id>/review")
def review_invoice(invoice_id):
    invoice = get_invoice(current_app.config["DATABASE_PATH"], invoice_id)
    if invoice is None:
        return jsonify({"error": "Invoice not found."}), 404

    payload = request.get_json(silent=True) or {}
    corrections = payload.get("fields", {})
    if not isinstance(corrections, dict):
        return jsonify({"error": "'fields' must be an object."}), 400

    extraction = invoice.get("extraction", {})
    for field, value in corrections.items():
        extraction[field] = {"value": value, "confidence": 1.0, "source": "reviewer"}

    pii_map = _read_json(invoice.get("pii_map_path"), default={})
    validation = InvoiceValidator().validate(extraction, pii_map)
    status = "completed" if validation["valid"] else "needs_review"

    updated = update_invoice(
        current_app.config["DATABASE_PATH"],
        invoice_id,
        status=status,
        extraction_json=json.dumps(extraction),
        validation_json=json.dumps(validation),
    )
    return jsonify(updated)


def _process_upload(file_storage):
    invoice_id = str(uuid.uuid4())
    original_filename = secure_filename(file_storage.filename)
    suffix = Path(original_filename).suffix.lower().lstrip(".")
    if suffix not in current_app.config["ALLOWED_EXTENSIONS"]:
        return {
            "id": invoice_id,
            "original_filename": original_filename,
            "status": "rejected",
            "error": f"Unsupported file type: {suffix}",
        }

    stored_filename = f"{invoice_id}-{original_filename}"
    upload_path = current_app.config["UPLOAD_DIR"] / stored_filename
    file_storage.save(upload_path)

    ocr_text, warnings = OcrService().extract_text(upload_path)
    ocr_text_path = current_app.config["TEXT_DIR"] / f"{invoice_id}.txt"
    ocr_text_path.write_text(ocr_text, encoding="utf-8")

    masker = PiiMasker()
    masking_result = masker.mask(ocr_text)
    masked_text_path = current_app.config["MASK_DIR"] / f"{invoice_id}.masked.txt"
    pii_map_path = current_app.config["MASK_DIR"] / f"{invoice_id}.pii-map.json"
    masked_text_path.write_text(masking_result.masked_text, encoding="utf-8")
    pii_map_path.write_text(json.dumps(masking_result.pii_map, indent=2), encoding="utf-8")

    try:
        extraction = InvoiceLlmClient(
            provider=current_app.config["LLM_PROVIDER"],
            model=_configured_model(),
            base_url=current_app.config["GENAILAB_BASE_URL"],
            verify_ssl=current_app.config["GENAILAB_VERIFY_SSL"],
            masker=masker,
        ).extract_invoice(masking_result.masked_text)
    except LlmPayloadRejected as exc:
        extraction = {}
        warnings.append(str(exc))
    except (LlmConfigurationError, LlmExtractionError) as exc:
        extraction = InvoiceExtractor().extract(masking_result.masked_text)
        warnings.append(f"{exc} Local masked-text extractor was used instead.")

    validation = InvoiceValidator().validate(extraction, masking_result.pii_map)
    if not ocr_text.strip():
        validation["errors"].append({"field": "ocr_text", "message": "No text could be extracted."})
        validation["valid"] = False

    status = "completed" if validation["valid"] else "needs_review"
    invoice = insert_invoice(
        current_app.config["DATABASE_PATH"],
        {
            "id": invoice_id,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "status": status,
            "upload_path": str(upload_path),
            "ocr_text_path": str(ocr_text_path),
            "masked_text_path": str(masked_text_path),
            "pii_map_path": str(pii_map_path),
            "extraction": extraction,
            "validation": validation,
            "warnings": warnings,
        },
    )
    invoice["pii"] = {
        "masked": True,
        "tokens_created": len(masking_result.pii_map),
        "kinds": sorted({item.kind for item in masking_result.findings}),
    }
    return invoice


def _read_json(path, default):
    if not path:
        return default
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _configured_model():
    if current_app.config["LLM_PROVIDER"] == "genailab":
        return current_app.config["GENAILAB_MODEL"]
    return current_app.config["OPENAI_MODEL"]
