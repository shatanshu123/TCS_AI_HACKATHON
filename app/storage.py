import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def connect(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path):
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                upload_path TEXT NOT NULL,
                ocr_text_path TEXT,
                masked_text_path TEXT,
                pii_map_path TEXT,
                file_blob BLOB,
                content_type TEXT,
                file_size INTEGER,
                extraction_json TEXT,
                validation_json TEXT,
                warnings_json TEXT
            )
            """
        )
        _ensure_column(connection, "invoices", "file_blob", "BLOB")
        _ensure_column(connection, "invoices", "content_type", "TEXT")
        _ensure_column(connection, "invoices", "file_size", "INTEGER")


def _ensure_column(connection, table_name, column_name, column_type):
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def insert_invoice(database_path, invoice):
    now = utc_now()
    payload = {
        "id": invoice["id"],
        "original_filename": invoice["original_filename"],
        "stored_filename": invoice["stored_filename"],
        "status": invoice["status"],
        "created_at": now,
        "updated_at": now,
        "upload_path": invoice["upload_path"],
        "ocr_text_path": invoice.get("ocr_text_path"),
        "masked_text_path": invoice.get("masked_text_path"),
        "pii_map_path": invoice.get("pii_map_path"),
        "file_blob": invoice.get("file_blob"),
        "content_type": invoice.get("content_type"),
        "file_size": invoice.get("file_size"),
        "extraction_json": json.dumps(invoice.get("extraction", {})),
        "validation_json": json.dumps(invoice.get("validation", {})),
        "warnings_json": json.dumps(invoice.get("warnings", [])),
    }

    with connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO invoices (
                id, original_filename, stored_filename, status, created_at, updated_at,
                upload_path, ocr_text_path, masked_text_path, pii_map_path,
                file_blob, content_type, file_size,
                extraction_json, validation_json, warnings_json
            )
            VALUES (
                :id, :original_filename, :stored_filename, :status, :created_at, :updated_at,
                :upload_path, :ocr_text_path, :masked_text_path, :pii_map_path,
                :file_blob, :content_type, :file_size,
                :extraction_json, :validation_json, :warnings_json
            )
            """,
            payload,
        )
    return get_invoice(database_path, invoice["id"])


def update_invoice(database_path, invoice_id, **changes):
    allowed = {
        "status",
        "ocr_text_path",
        "masked_text_path",
        "pii_map_path",
        "extraction_json",
        "validation_json",
        "warnings_json",
    }
    assignments = []
    params = {"id": invoice_id, "updated_at": utc_now()}

    for key, value in changes.items():
        if key not in allowed:
            continue
        assignments.append(f"{key} = :{key}")
        params[key] = value

    if not assignments:
        return get_invoice(database_path, invoice_id)

    assignments.append("updated_at = :updated_at")

    with connect(database_path) as connection:
        connection.execute(
            f"UPDATE invoices SET {', '.join(assignments)} WHERE id = :id",
            params,
        )

    return get_invoice(database_path, invoice_id)


def list_invoices(database_path):
    with connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, original_filename, status, created_at, updated_at,
                   content_type, file_size,
                   extraction_json, validation_json, warnings_json
            FROM invoices
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [serialize_invoice(row, include_paths=False) for row in rows]


def get_invoice(database_path, invoice_id):
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
    if row is None:
        return None
    return serialize_invoice(row)


def get_invoice_file(database_path, invoice_id):
    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT original_filename, content_type, file_size, file_blob
            FROM invoices
            WHERE id = ?
            """,
            (invoice_id,),
        ).fetchone()
    if row is None or row["file_blob"] is None:
        return None
    return {
        "filename": row["original_filename"],
        "content_type": row["content_type"] or "application/octet-stream",
        "file_size": row["file_size"],
        "content": row["file_blob"],
    }


def serialize_invoice(row, include_paths=True):
    invoice = {
        "id": row["id"],
        "original_filename": row["original_filename"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "database_storage": {
            "invoice_blob_stored": _row_has(row, "file_size") and row["file_size"] is not None,
            "content_type": row["content_type"] if _row_has(row, "content_type") else None,
            "file_size": row["file_size"] if _row_has(row, "file_size") else None,
        },
        "extraction": json.loads(row["extraction_json"] or "{}"),
        "validation": json.loads(row["validation_json"] or "{}"),
        "warnings": json.loads(row["warnings_json"] or "[]"),
    }
    if include_paths:
        invoice.update(
            {
                "stored_filename": row["stored_filename"],
                "upload_path": row["upload_path"],
                "ocr_text_path": row["ocr_text_path"],
                "masked_text_path": row["masked_text_path"],
                "pii_map_path": row["pii_map_path"],
            }
        )
    return invoice


def _row_has(row, key):
    return key in row.keys()
