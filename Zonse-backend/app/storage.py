import os
import re
import tempfile
import uuid
import warnings
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import settings

_SUPPORTED_IMAGE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}
_MANAGED_IMAGE_NAME = re.compile(r"[0-9a-f]{32}\.(?:jpg|png|webp)\Z")
_UPLOAD_CHUNK_SIZE = 64 * 1024


def store_property_image(upload: UploadFile) -> tuple[str, Path]:
    upload_directory = settings.UPLOAD_DIR
    upload_directory.mkdir(parents=True, exist_ok=True)
    staged_path: Path | None = None
    stored_path: Path | None = None
    completed = False

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".property-image-",
            suffix=".tmp",
            dir=upload_directory,
            delete=False,
        ) as staged_file:
            staged_path = Path(staged_file.name)
            byte_count = 0
            while chunk := upload.file.read(_UPLOAD_CHUNK_SIZE):
                byte_count += len(chunk)
                if byte_count > settings.MAX_IMAGE_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Image exceeds the configured upload-size limit",
                    )
                staged_file.write(chunk)

        if byte_count == 0:
            raise HTTPException(status_code=400, detail="Image file is empty")

        image_format = _validate_image(staged_path)
        extension = _SUPPORTED_IMAGE_FORMATS[image_format]
        while True:
            filename = f"{uuid.uuid4().hex}{extension}"
            stored_path = upload_directory / filename
            try:
                os.link(staged_path, stored_path)
                break
            except FileExistsError:
                continue

        staged_path.unlink()
        staged_path = None
        completed = True
        return f"/uploads/{filename}", stored_path
    finally:
        if staged_path is not None:
            staged_path.unlink(missing_ok=True)
        if not completed and stored_path is not None:
            stored_path.unlink(missing_ok=True)


def _validate_image(path: Path) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                image_format = image.format
                if image_format not in _SUPPORTED_IMAGE_FORMATS:
                    raise HTTPException(
                        status_code=415,
                        detail="Supported image formats are JPEG, PNG, and WebP",
                    )
                image.verify()
            with Image.open(path) as image:
                image.load()
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail="Image content is malformed or unsafe",
        ) from exc

    return image_format


def managed_image_path(image_url: str) -> Path | None:
    parsed_url = urlsplit(image_url)
    if (
        parsed_url.scheme
        or parsed_url.netloc
        or parsed_url.query
        or parsed_url.fragment
        or not parsed_url.path.startswith("/uploads/")
    ):
        return None

    filename = parsed_url.path.removeprefix("/uploads/")
    if _MANAGED_IMAGE_NAME.fullmatch(filename) is None:
        return None

    upload_directory = settings.UPLOAD_DIR.resolve()
    image_path = upload_directory / filename
    if image_path.is_symlink() or image_path.resolve().parent != upload_directory:
        return None
    return image_path if image_path.is_file() else None
