# 5일차 환자 관리 및 진료기록 API 설계

## 1. 문서 목적

- Stage 5 범위의 환자 관리 API와 진료기록 API를 한 문서에서 확인할 수 있도록 정리한다.
- 구현 전에 팀이 합의해야 하는 계약, 권한, 검증, 응답 규칙을 고정한다.
- 2026-07-21 기준 실제 구현과 수동 검증 결과를 반영한다.

---

## 2. 최종 범위

| 도메인 | Method | Path | 설명 |
| --- | --- | --- | --- |
| Patient | `POST` | `/api/v1/patients` | 환자 등록 |
| Patient | `GET` | `/api/v1/patients` | 환자 목록 조회 |
| Patient | `GET` | `/api/v1/patients/{patient_id}` | 환자 상세 조회 |
| Patient | `PATCH` | `/api/v1/patients/{patient_id}` | 환자 정보 수정 |
| Patient | `DELETE` | `/api/v1/patients/{patient_id}` | 환자 삭제 |
| Medical Record | `POST` | `/api/v1/patients/{patient_id}/medical-records` | 진료기록 등록 |
| Medical Record | `GET` | `/api/v1/patients/{patient_id}/medical-records` | 진료기록 목록 조회 |
| Medical Record | `GET` | `/api/v1/patients/{patient_id}/medical-records/{record_id}` | 진료기록 상세 조회 |

이번 Stage에서 제외:

- 진료기록 수정 API
- 진료기록 삭제 API

---

## 3. 권한 규칙

현재 인증 모델:

- `role`: `PENDING`, `STAFF`, `ADMIN`
- `department`: `MEDICAL`, `DEV`, `RESEARCH`

요구사항 표현을 현재 코드에 매핑하면 다음과 같다.

| 요구사항 표현 | 현재 코드 매핑 |
| --- | --- |
| 로그인 된 사내 개발진, 의료 실무진, 연구진 | `role in {STAFF, ADMIN}` |
| 사내 의료인 | `department == MEDICAL` 이고 `role in {STAFF, ADMIN}` |

권한 매트릭스:

| API | 허용 대상 | 공통 dependency |
| --- | --- | --- |
| 환자 등록 | `MEDICAL + STAFF`, `ADMIN` | `require_medical_staff_or_admin()` |
| 환자 목록/상세 조회 | `STAFF`, `ADMIN` | `require_staff_or_admin()` |
| 환자 수정/삭제 | `STAFF`, `ADMIN` | `require_staff_or_admin()` |
| 진료기록 등록 | `MEDICAL + STAFF`, `ADMIN` | `require_medical_staff_or_admin()` |
| 진료기록 목록/상세 조회 | `STAFF`, `ADMIN` | `require_staff_or_admin()` |

공통 원칙:

- JWT 파싱은 router에서 직접 처리하지 않는다.
- `PENDING` 사용자는 이번 Stage API 전체 접근 불가다.
- 오류 응답은 프로젝트 전역 예외 처리 규칙을 그대로 따른다.

---

## 4. 공통 규칙

### 4.1 URL 및 ID

- Base URL: `/api/v1`
- 리소스명은 복수형 사용
- 환자 리소스: `/patients`
- 진료기록 리소스: `/patients/{patient_id}/medical-records`
- `patient_id`, `record_id`는 1 이상의 정수

### 4.2 시간 및 정렬

- DB 저장 기준은 UTC
- API 응답은 ISO 8601 형식
- 환자 목록 정렬: `created_at DESC`, `id DESC`
- 진료기록 목록 정렬: `created_at DESC`, `id DESC`

### 4.3 페이지네이션

- `offset`, `limit` 방식 사용
- 기본값: `offset=0`, `limit=20`
- 최대 `limit=100`

### 4.4 오류 응답 포맷

```json
{
  "code": "PATIENT_NOT_FOUND",
  "message": "Patient not found"
}
```

대표 오류 코드:

| 상황 | 상태 코드 | 오류 코드 |
| --- | --- | --- |
| 인증 누락 | `401` | `AUTHENTICATION_REQUIRED` |
| 권한 부족 | `403` | `PERMISSION_DENIED` |
| 환자 없음 | `404` | `PATIENT_NOT_FOUND` |
| 진료기록 없음 | `404` | `MEDICAL_RECORD_NOT_FOUND` |
| 차트 번호 중복 | `409` | `DUPLICATE_CHART_NUMBER` |
| 유효성 검증 실패 | `422` | `VALIDATION_ERROR` |
| 잘못된 X-Ray 파일 | `422` | `INVALID_XRAY_FILE` |
| X-Ray 파일 크기 초과 | `422` | `XRAY_FILE_TOO_LARGE` |
| 서버 내부 오류 | `500` | `INTERNAL_SERVER_ERROR` |
| 요청 시간 초과 | `504` | `REQUEST_TIMEOUT` |

### 4.5 입력 검증

| 필드 | 규칙 |
| --- | --- |
| `name` | 앞뒤 공백 제거 후 1~50자 |
| `age` | 0~150 |
| `gender` | `M`, `F`만 허용 |
| `phone` | 숫자와 하이픈 허용, 저장 시 숫자만 유지 |
| `chart_number` | 앞뒤 공백 제거 후 1~50자 |
| `symptoms` | 1~5000자 |
| `xray` | `jpg`, `jpeg`, `png`만 허용, 최대 10MB |

연락처 정규화 예시:

- 입력: `010-1234-5678`
- 저장/응답: `01012345678`

### 4.6 파일 저장 규칙

| 항목 | 값 |
| --- | --- |
| 로컬 저장 경로 | `uploads/xrays/{patient_id}/{uuid}.{extension}` |
| DB 저장값 | `xrays/{patient_id}/{uuid}.{extension}` |
| 응답 URL | `/uploads/xrays/{patient_id}/{uuid}.{extension}` |

파일 처리 순서:

1. 환자 존재 확인
2. 확장자 및 크기 검증
3. 파일 저장
4. DB 레코드 생성
5. DB 실패 시 저장된 파일 삭제

환자 삭제 시:

1. 연결된 X-Ray 경로 수집
2. 환자 및 연관 DB 데이터 삭제
3. commit 성공 후 실제 파일 삭제
4. 파일이 이미 없어도 삭제 성공 처리

---

## 5. 데이터 모델 계약

### 5.1 Patients

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `id` | int | PK |
| `name` | varchar(50) | required |
| `age` | int | required |
| `gender` | enum(`M`, `F`) | required |
| `phone` | varchar(20) | required |
| `created_at` | datetime | required |
| `updated_at` | datetime | nullable |

### 5.2 MedicalRecord

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `id` | int | PK |
| `patient_id` | int | FK, required |
| `chart_number` | varchar(50) | required, unique |
| `symptoms` | text | required |
| `created_at` | datetime | required |
| `updated_at` | datetime | nullable |

### 5.3 XrayImage

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `id` | int | PK |
| `record_id` | int | FK, required |
| `uploader_id` | int | nullable |
| `image_url` | varchar | required |
| `shooting_datetime` | datetime | required |
| `created_at` | datetime | required |

관계 규칙:

- `Patient 1 : N MedicalRecord`
- `MedicalRecord 1 : N XrayImage`
- 이번 Stage에서는 진료기록 등록 시 X-Ray 이미지는 1개만 업로드 받는다.

---

## 6. API 상세 명세

### 6.1 환자 등록

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| Path | `/api/v1/patients` |
| 권한 | `MEDICAL + STAFF`, `ADMIN` |
| Content-Type | `application/json` |

Request:

```json
{
  "name": "홍길동",
  "age": 35,
  "gender": "M",
  "phone": "010-1234-5678"
}
```

Success:

- `201 Created`

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 35,
  "gender": "M",
  "phone": "01012345678",
  "created_at": "2026-07-21T07:00:00Z",
  "updated_at": null
}
```

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `422 VALIDATION_ERROR`

### 6.2 환자 목록 조회

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| Path | `/api/v1/patients` |
| 권한 | `STAFF`, `ADMIN` |

Query:

| 필드 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `name` | string | 없음 | 이름 부분 검색 |
| `gender` | string | 없음 | `M`, `F` 필터 |
| `min_age` | integer | 없음 | 최소 나이 |
| `max_age` | integer | 없음 | 최대 나이 |
| `offset` | integer | `0` | 조회 시작 위치 |
| `limit` | integer | `20` | 조회 건수 |

Success:

- `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "name": "홍길동",
      "age": 35,
      "gender": "M",
      "phone": "01012345678",
      "created_at": "2026-07-21T07:00:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 20
}
```

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `422 VALIDATION_ERROR`

### 6.3 환자 상세 조회

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| Path | `/api/v1/patients/{patient_id}` |
| 권한 | `STAFF`, `ADMIN` |

Success:

- `200 OK`

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 35,
  "gender": "M",
  "phone": "01012345678",
  "created_at": "2026-07-21T07:00:00Z",
  "updated_at": null
}
```

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `404 PATIENT_NOT_FOUND`

### 6.4 환자 수정

| 항목 | 내용 |
| --- | --- |
| Method | `PATCH` |
| Path | `/api/v1/patients/{patient_id}` |
| 권한 | `STAFF`, `ADMIN` |
| Content-Type | `application/json` |

허용 필드:

- `name`
- `phone`

Request:

```json
{
  "name": "홍길순",
  "phone": "010-9999-0000"
}
```

Success:

- `200 OK`

```json
{
  "id": 1,
  "name": "홍길순",
  "age": 35,
  "gender": "M",
  "phone": "01099990000",
  "created_at": "2026-07-21T07:00:00Z",
  "updated_at": "2026-07-21T08:30:00Z"
}
```

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `404 PATIENT_NOT_FOUND`
- `422 VALIDATION_ERROR`
- `500 INTERNAL_SERVER_ERROR`

### 6.5 환자 삭제

| 항목 | 내용 |
| --- | --- |
| Method | `DELETE` |
| Path | `/api/v1/patients/{patient_id}` |
| 권한 | `STAFF`, `ADMIN` |

Success:

- `204 No Content`

삭제 범위:

1. 환자 정보
2. 연관 진료기록
3. 연관 X-Ray DB 데이터
4. 로컬 X-Ray 파일

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `404 PATIENT_NOT_FOUND`
- `422 VALIDATION_ERROR`
- `500 INTERNAL_SERVER_ERROR`

### 6.6 진료기록 등록

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| Path | `/api/v1/patients/{patient_id}/medical-records` |
| 권한 | `MEDICAL + STAFF`, `ADMIN` |
| Content-Type | `multipart/form-data` |

Form Data:

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| `chart_number` | text | Y |
| `symptoms` | text | Y |
| `xray` | file | Y |

Success:

- `201 Created`

```json
{
  "id": 1,
  "patient_id": 1,
  "chart_number": "XR-2026-0001",
  "symptoms": "기침 및 흉통",
  "xray_url": "/uploads/xrays/1/d5124467-c392-42b7-9483-b7b45523d5d7.jpg",
  "created_at": "2026-07-21T10:10:24",
  "updated_at": null
}
```

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `404 PATIENT_NOT_FOUND`
- `409 DUPLICATE_CHART_NUMBER`
- `422 INVALID_XRAY_FILE`
- `422 XRAY_FILE_TOO_LARGE`
- `422 VALIDATION_ERROR`
- `504 REQUEST_TIMEOUT`

### 6.7 진료기록 목록 조회

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| Path | `/api/v1/patients/{patient_id}/medical-records` |
| 권한 | `STAFF`, `ADMIN` |

Query:

| 필드 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `offset` | integer | `0` | 건너뛸 진료기록 수 |
| `limit` | integer | `20` | 최대 조회 건수 |

Success:

- `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "chart_number": "XR-2026-0001",
      "symptoms": "기침 및 흉통",
      "created_at": "2026-07-21T10:10:24"
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 20
}
```

추가 규칙:

- 환자는 존재하지만 진료기록이 없으면 `200 OK`와 빈 배열 반환
- `symptoms`가 100자를 초과하면 응답에서만 `앞 100자...` 형태로 축약

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `404 PATIENT_NOT_FOUND`
- `422 VALIDATION_ERROR`
- `500 INTERNAL_SERVER_ERROR`

### 6.8 진료기록 상세 조회

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| Path | `/api/v1/patients/{patient_id}/medical-records/{record_id}` |
| 권한 | `STAFF`, `ADMIN` |

Success:

- `200 OK`

```json
{
  "id": 1,
  "patient_id": 1,
  "chart_number": "XR-2026-0001",
  "symptoms": "기침 및 흉통",
  "xray_url": "/uploads/xrays/1/d5124467-c392-42b7-9483-b7b45523d5d7.jpg",
  "created_at": "2026-07-21T10:10:24"
}
```

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `404 PATIENT_NOT_FOUND`
- `404 MEDICAL_RECORD_NOT_FOUND`
- `422 VALIDATION_ERROR`
- `500 INTERNAL_SERVER_ERROR`

추가 규칙:

- `patient_id`와 `record_id`를 함께 검증한다.
- 다른 환자에게 속한 `record_id`는 `404 MEDICAL_RECORD_NOT_FOUND` 처리한다.
- `xray_url`은 DB 상대 경로를 `/uploads/...` 형식으로 변환해 응답한다.

---

## 7. 로컬 검증 결과

2026-07-21 기준 수동 검증 확인 항목:

- 환자 생성 성공
- 환자 목록 조회 성공
- 환자 상세 조회 성공
- 환자 수정 성공
- 환자 삭제 성공
- 진료기록 등록 성공
- 진료기록 목록 조회 성공
- 진료기록 상세 조회 성공
- 환자 삭제 후 환자 재조회 `404 PATIENT_NOT_FOUND`
- 환자 삭제 후 진료기록 상세 재조회 `404 PATIENT_NOT_FOUND`

---

## 8. 구현 메모

공통으로 사용되는 함수 및 계층:

- `get_patient_or_404()`
- `get_medical_record_or_404()`
- `require_staff_or_admin()`
- `require_medical_staff_or_admin()`
- `normalize_phone()`
- `save_xray_file()`
- `delete_xray_file()`

이번 Stage에서 공통적으로 정리된 파일 범위:

- `app/models/patients.py`
- `app/models/medical_records.py`
- `app/models/xray_image.py`
- `app/schemas/patient.py`
- `app/schemas/medical_record.py`
- `app/schemas/common.py`
- `app/apis/dependencies.py`
- `app/services/file_storage.py`
- `app/utils/validators.py`
