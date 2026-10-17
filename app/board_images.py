"""Decode bounded homework photos and retain pixels only, without metadata."""

from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PHOTO_PIXELS = 16_000_000


def normalize_photo(raw: bytes) -> bytes:
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Choose a photo smaller than 5 MB")
    try:
        with Image.open(BytesIO(raw), formats=["JPEG", "PNG"]) as source:
            if source.width * source.height > MAX_PHOTO_PIXELS:
                raise HTTPException(413, "Photo dimensions are too large")
            if getattr(source, "n_frames", 1) != 1:
                raise HTTPException(422, "Choose a still JPEG or PNG photo")
            source.load()
            oriented = ImageOps.exif_transpose(source)
            oriented.thumbnail((1600, 1000))
            # Fresh pixels discard EXIF/GPS, comments, profiles, and filenames.
            rgba = oriented.convert("RGBA")
            pixels = Image.new("RGB", rgba.size, "white")
            pixels.paste(rgba, mask=rgba.getchannel("A"))
            output = BytesIO()
            pixels.save(output, format="JPEG", quality=90)
            return output.getvalue()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, "Choose a valid JPEG or PNG photo") from exc
