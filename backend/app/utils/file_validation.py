"""
Upload validation helpers: extension whitelisting, size limits, and
safe/sanitized filenames to prevent path traversal.
"""
import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationAppError

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name  # strip any directory components
    name = _SAFE_NAME_RE.sub("_", name).strip("._") or "file"
    return name[:200]


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValidationAppError(
            f"File type '{ext or 'unknown'}' is not supported. "
            f"Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    return ext


async def save_upload(upload: UploadFile, destination_dir: Path) -> tuple[str, Path]:
    """Validate, then stream an UploadFile to disk under a random,
    collision-free name. Returns (original_display_name, saved_path)."""
    validate_extension(upload.filename or "")
    safe_name = sanitize_filename(upload.filename or "file")

    destination_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest_path = destination_dir / unique_name

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    size = 0
    chunk_size = 1024 * 1024

    with open(dest_path, "wb") as out_file:
        while True:
            chunk = await upload.read(chunk_size)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                out_file.close()
                dest_path.unlink(missing_ok=True)
                raise ValidationAppError(
                    f"File '{upload.filename}' exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit."
                )
            out_file.write(chunk)

    await upload.close()
    return safe_name, dest_path


def resolve_safe_local_path(raw_path: str) -> Path:
    """Used only by the (opt-in, disabled-by-default) legacy path-based
    compare endpoint. Ensures the resolved path stays within
    settings.ALLOWED_LOCAL_ROOT — blocks `../` traversal and absolute
    paths outside the sandboxed root."""
    root = settings.ALLOWED_LOCAL_ROOT.resolve()
    candidate = (root / raw_path).resolve()

    if root not in candidate.parents and candidate != root:
        raise ValidationAppError(f"Path '{raw_path}' is outside the allowed directory.")

    return candidate
