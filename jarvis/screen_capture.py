"""Privacy-gated screenshot capture; never saves or transmits an image."""
import io
import os


def capture_screen_png(max_bytes=15_000_000):
    if os.name != "nt":
        raise OSError("Screen capture is supported only on Windows")
    if not 0 < max_bytes <= 30_000_000:
        raise ValueError("Invalid screenshot size limit")
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise RuntimeError("Pillow is required for screenshot capture") from exc
    image = ImageGrab.grab()
    buffer = io.BytesIO()
    try:
        image.save(buffer, format="PNG")
        result = buffer.getvalue()
        if len(result) > max_bytes:
            raise ValueError("Screenshot exceeds configured size limit")
        return result
    finally:
        image.close()
        buffer.close()
