from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.auth.exceptions import FileStorageError
from app.utils.validators import validate_xray_file


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = BASE_DIR / "uploads"
XRAY_ROOT = UPLOAD_ROOT / "xrays"


async def save_xray_file(patient_id: int, upload_file: UploadFile) -> str:
    validate_xray_file(upload_file)

    extension = Path(upload_file.filename or "").suffix.lower()
    filename = f"{uuid4()}{extension}"
    relative_path = Path("xrays") / str(patient_id) / filename
    full_path = UPLOAD_ROOT / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        contents = await upload_file.read()
        with full_path.open("wb") as file_obj:
            file_obj.write(contents)
    except OSError as exc:
        raise FileStorageError() from exc
    finally:
        await upload_file.close()

    return relative_path.as_posix()


def delete_xray_file(relative_path: str) -> None:
    target = UPLOAD_ROOT / relative_path
    try:
        if target.exists():
            target.unlink()
    except OSError:
        return

    parent = target.parent
    if parent == XRAY_ROOT:
        return
    try:
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    except OSError:
        return
