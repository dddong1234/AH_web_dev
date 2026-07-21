import re
from pathlib import Path

from fastapi import UploadFile

from app.core.auth.exceptions import InvalidXrayFileError, XrayFileTooLargeError


ALLOWED_XRAY_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_XRAY_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_XRAY_SIZE_BYTES = 10 * 1024 * 1024


def normalize_phone(value: str) -> str:
    cleaned = re.sub(r"\D", "", value)
    if len(cleaned) != 11 or not cleaned.startswith("010"):
        raise ValueError("휴대폰 번호는 010으로 시작하는 11자리 숫자여야 합니다.")
    return cleaned


def truncate_symptoms(value: str, max_length: int = 100) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def validate_xray_file(upload_file: UploadFile) -> None:
    extension = Path(upload_file.filename or "").suffix.lower()
    if extension not in ALLOWED_XRAY_EXTENSIONS:
        raise InvalidXrayFileError()

    if upload_file.content_type not in ALLOWED_XRAY_CONTENT_TYPES:
        raise InvalidXrayFileError()

    file_obj = upload_file.file
    current_position = file_obj.tell()
    file_obj.seek(0, 2)
    size = file_obj.tell()
    file_obj.seek(current_position)

    if size > MAX_XRAY_SIZE_BYTES:
        raise XrayFileTooLargeError()


def build_xray_url(relative_path: str) -> str:
    return f"/uploads/{relative_path.lstrip('/')}"
