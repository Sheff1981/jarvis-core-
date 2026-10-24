"""Local OCR only. No image uploads, logs, or screenshot files."""
import io


def recognize_screen_text(png_bytes, max_chars=3000):
    if not isinstance(png_bytes, bytes) or not png_bytes:
        raise ValueError("Nonempty PNG bytes are required")
    if not 1 <= max_chars <= 10000:
        raise ValueError("Invalid OCR text limit")
    try:
        from PIL import Image
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("Local OCR requires Pillow and pytesseract") from exc
    with Image.open(io.BytesIO(png_bytes)) as image:
        text = pytesseract.image_to_string(image, lang="rus+eng")
    return text.strip()[:max_chars]
