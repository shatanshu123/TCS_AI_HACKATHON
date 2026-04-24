import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage")).resolve()
    UPLOAD_DIR = STORAGE_DIR / "uploads"
    TEXT_DIR = STORAGE_DIR / "texts"
    MASK_DIR = STORAGE_DIR / "masked"
    DATABASE_PATH = STORAGE_DIR / "invoices.sqlite3"

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tif", "tiff", "txt"}
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local").lower()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    GENAILAB_BASE_URL = os.getenv("GENAILAB_BASE_URL", "https://genailab.tcs.in")
    GENAILAB_MODEL = os.getenv("GENAILAB_MODEL", "azure_ai/genailab-maas-DeepSeek-V3-0324")
    GENAILAB_VERIFY_SSL = os.getenv("GENAILAB_VERIFY_SSL", "false").lower() == "true"

    @classmethod
    def ensure_directories(cls):
        for directory in (cls.STORAGE_DIR, cls.UPLOAD_DIR, cls.TEXT_DIR, cls.MASK_DIR):
            directory.mkdir(parents=True, exist_ok=True)
