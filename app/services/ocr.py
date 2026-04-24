from pathlib import Path


class OcrService:
    def extract_text(self, file_path):
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".txt":
            return path.read_text(encoding="utf-8", errors="ignore"), []

        if suffix == ".pdf":
            return self._extract_pdf(path)

        if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
            return self._extract_image(path)

        return "", [f"Unsupported file type: {suffix}"]

    def _extract_pdf(self, path):
        try:
            from pypdf import PdfReader
        except ImportError:
            return "", ["PDF OCR skipped: install pypdf to extract embedded PDF text."]

        try:
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            warnings = []
            if not text:
                warnings.append("No embedded PDF text found. Use image OCR for scanned PDFs.")
            return text, warnings
        except Exception as exc:
            return "", [f"PDF extraction failed: {exc}"]

    def _extract_image(self, path):
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            return "", ["Image OCR skipped: install Pillow and pytesseract."]

        try:
            with Image.open(path) as image:
                text = pytesseract.image_to_string(image)
            return text.strip(), []
        except Exception as exc:
            return "", [f"Image OCR failed: {exc}"]

