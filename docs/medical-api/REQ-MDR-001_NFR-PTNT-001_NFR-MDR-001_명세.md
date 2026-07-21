# REQ-MDR-001 - 진료기록 등록 및 성능(NFR) API 명세서

## 1. API 개요 (진료기록 및 X-Ray 이미지 등록)

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-MDR-001 |
| API 이름 | 진료기록 및 X-Ray 이미지 등록 API |
| 설명 | 환자의 X-Ray 사진을 포함한 진료기록을 로컬 저장소에 저장하고 등록하는 API |
| 엔드포인트(Endpoint) | `/api/v1/patients/{patient_id}/medical-records` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | Y (Bearer JWT) |
| 허용 권한 | 사내 의료인 (`department == MEDICAL` 이고 `role in {STAFF, ADMIN}`) |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {token} | JWT 액세스 토큰 |
| Content-Type | multipart/form-data | 요청 타입 |

### Path Parameters

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 대상 환자 고유 ID |

### Form Data 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| chart_number | string | Y | 진료 차트 넘버 (앞뒤 공백 제거 후 1~50자, 시스템 전역 Unique) |
| symptoms | string | Y | 진료된 증상 (1~5000자) |
| xray | file | Y | 흉부 X-Ray 이미지 (`jpg`, `jpeg`, `png`만 허용, 최대 10MB) |

---

## 3. 응답(Response)

### 성공

- 201 Created

    ```json
    {
      "id": 1,
      "patient_id": 12,
      "chart_number": "XR-2026-0001",
      "symptoms": "기침 및 흉통",
      "xray_url": "/uploads/xrays/12/550e8400-e29b-41d4-a716-446655440000.png",
      "created_at": "2026-07-21T07:00:00Z",
      "updated_at": "2026-07-21T07:00:00Z"
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | id | integer | 생성된 진료기록 고유 ID |
    | patient_id | integer | 대상 환자 고유 ID |
    | chart_number | string | 진료 차트 넘버 |
    | symptoms | string | 진료 증상 |
    | xray_url | string | X-Ray 이미지 서빙/미리보기 상대 경로 |
    | created_at | string (ISO 8601) | 생성일시 (UTC) |
    | updated_at | string (ISO 8601) | 수정일시 (UTC) |

### 실패

- 401 Unauthorized

    ```json
    {
      "code": "UNAUTHORIZED",
      "message": "인증 토큰이 유효하지 않거나 만료되었습니다."
    }
    ```

- 403 Forbidden

    ```json
    {
      "code": "FORBIDDEN",
      "message": "사내 의료인 권한이 필요합니다."
    }
    ```

- 404 Not Found

    ```json
    {
      "code": "PATIENT_NOT_FOUND",
      "message": "Patient not found"
    }
    ```

- 409 Conflict

    ```json
    {
      "code": "DUPLICATE_CHART_NUMBER",
      "message": "Chart number already exists"
    }
    ```

- 422 Unprocessable Entity

    ```json
    {
      "code": "INVALID_XRAY_FILE",
      "message": "Only JPG, JPEG and PNG files are allowed"
    }
    ```

---

## 4. 파일 저장 규칙

| 항목 | 내용 |
| --- | --- |
| 로컬 물리 저장 경로 | `uploads/xrays/{patient_id}/{uuid}.{extension}` |
| DB 저장값 | `xrays/{patient_id}/{uuid}.{extension}` (상대 경로만 저장) |
| 응답 서빙 경로 (`xray_url`) | `/uploads/xrays/{patient_id}/{uuid}.{extension}` |

---

## 5. 비기능 요구사항 명세 (NFR)

### 5.1 환자 API 성능 (NFR-PTNT-001)

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | NFR-PTNT-001 |
| 목표 SLA | 환자 관리 유저 API 최대 3초 이내 응답 처리 |
| 구현 방식 | `AsyncSession` 비동기 DB 커넥션 및 인덱싱 활용, 3초 초과 시 `504 Gateway Timeout` (`RequestTimeoutError`) |

### 5.2 진료기록 API 성능 (NFR-MDR-001)

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | NFR-MDR-001 |
| 목표 SLA | 진료기록 유저 API 최대 3초 이내 응답 처리 |
| 구현 방식 | `aiofiles` 기반 대용량 X-Ray 파일 비동기 스트리밍 업로드, 3초 초과 시 `504 Gateway Timeout` (`RequestTimeoutError`) |
