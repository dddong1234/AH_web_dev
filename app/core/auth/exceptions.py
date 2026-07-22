class AppBaseException(Exception):
    status_code: int = 500
    code: str = "INTERNAL_SERVER_ERROR"
    message: str = "서버 내부 오류가 발생했습니다."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class ValidationErrorException(AppBaseException):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "요청 데이터 유효성 검증에 실패했습니다."


class AuthenticationRequiredError(AppBaseException):
    status_code = 401
    code = "AUTHENTICATION_REQUIRED"
    message = "로그인이 필요합니다."


class InvalidCredentialsError(AppBaseException):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    message = "이메일 또는 비밀번호가 올바르지 않습니다."


class InvalidAccessTokenError(AppBaseException):
    status_code = 401
    code = "INVALID_ACCESS_TOKEN"
    message = "유효하지 않은 Access Token입니다."


class AccessTokenExpiredError(AppBaseException):
    status_code = 401
    code = "ACCESS_TOKEN_EXPIRED"
    message = "Access Token이 만료되었습니다."


class RefreshTokenRequiredError(AppBaseException):
    status_code = 401
    code = "REFRESH_TOKEN_REQUIRED"
    message = "Refresh Token이 필요합니다."


class InvalidRefreshTokenError(AppBaseException):
    status_code = 401
    code = "INVALID_REFRESH_TOKEN"
    message = "유효하지 않은 Refresh Token입니다."


class RefreshTokenExpiredError(AppBaseException):
    status_code = 401
    code = "REFRESH_TOKEN_EXPIRED"
    message = "로그인이 만료되었습니다. 다시 로그인해 주세요."


class RefreshTokenRevokedError(AppBaseException):
    status_code = 401
    code = "REFRESH_TOKEN_REVOKED"
    message = "사용할 수 없는 Refresh Token입니다."


class InactiveUserError(AppBaseException):
    status_code = 403
    code = "INACTIVE_USER"
    message = "비활성화된 계정입니다."


class UserNotFoundError(AppBaseException):
    status_code = 401
    code = "USER_NOT_FOUND"
    message = "사용자를 찾을 수 없습니다."


class PermissionDeniedError(AppBaseException):
    status_code = 403
    code = "PERMISSION_DENIED"
    message = "접근 권한이 없습니다."


class EmailAlreadyExistsError(AppBaseException):
    status_code = 409
    code = "EMAIL_ALREADY_EXISTS"
    message = "이미 사용 중인 이메일 주소입니다."


class PhoneNumberAlreadyExistsError(AppBaseException):
    status_code = 409
    code = "PHONE_NUMBER_ALREADY_EXISTS"
    message = "이미 사용 중인 휴대폰 번호입니다."


class CurrentPasswordMismatchError(AppBaseException):
    status_code = 400
    code = "CURRENT_PASSWORD_MISMATCH"
    message = "기존 비밀번호가 일치하지 않습니다."


class RequestTimeoutError(AppBaseException):
    status_code = 504
    code = "REQUEST_TIMEOUT"
    message = "요청 처리 시간이 허용 시간(3초)을 초과하였습니다."


class PatientNotFoundError(AppBaseException):
    status_code = 404
    code = "PATIENT_NOT_FOUND"
    message = "Patient not found"


class MedicalRecordNotFoundError(AppBaseException):
    status_code = 404
    code = "MEDICAL_RECORD_NOT_FOUND"
    message = "Medical record not found"


class DuplicateChartNumberError(AppBaseException):
    status_code = 409
    code = "DUPLICATE_CHART_NUMBER"
    message = "Chart number already exists"


class InvalidXrayFileError(AppBaseException):
    status_code = 422
    code = "INVALID_XRAY_FILE"
    message = "Only JPG, JPEG and PNG files are allowed"


class XrayFileTooLargeError(AppBaseException):
    status_code = 422
    code = "XRAY_FILE_TOO_LARGE"
    message = "X-Ray image must be 10MB or smaller"


class EmptyUpdatePayloadError(AppBaseException):
    status_code = 422
    code = "EMPTY_UPDATE_PAYLOAD"
    message = "At least one field is required"


class FileStorageError(AppBaseException):
    status_code = 500
    code = "FILE_STORAGE_ERROR"
    message = "Failed to store X-Ray image"


class XrayImageNotFoundError(AppBaseException):
    status_code = 422
    code = "XRAY_IMAGE_NOT_FOUND"
    message = "X-Ray image not found"


class AIInferenceFailedError(AppBaseException):
    status_code = 500
    code = "AI_INFERENCE_FAILED"
    message = "AI inference failed"


class HeatmapStorageFailedError(AppBaseException):
    status_code = 500
    code = "HEATMAP_STORAGE_FAILED"
    message = "Failed to store Grad-CAM heatmap"
