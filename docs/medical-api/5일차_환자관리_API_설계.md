# 5일차 환자 관리 및 진료기록 API 설계

## 1. 문서 목적

- 이 문서는 2026-07-21 기준 Stage 5 구현 전에 팀이 먼저 고정해야 하는 API 계약과 공통 규칙을 정리한다.
- 사람이 읽고 바로 구현 범위를 이해할 수 있어야 하고, 에이전트에게 그대로 전달해도 작업 단위가 분리되도록 작성한다.
- 본 문서는 Notion의 `Stage 5` 페이지와 `5일차 - 진료기록 사용자 요구사항 정의서`를 기준으로 정리한다.

---

## 2. 최종 구현 범위

### 필수 API

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

### 이번 Stage에서 제외

- 진료기록 수정 API
- 진료기록 삭제 API

제외 이유:
- Notion Stage 5 완료 조건은 위 8개 API 구현과 문서화만으로 충족 가능하다.
- 범위를 줄여 병합 충돌과 스키마 재변경 가능성을 낮춘다.

---

## 3. 요구사항을 현재 인증 모델에 매핑하는 규칙

현재 코드베이스의 인증 모델은 다음 두 축을 가진다.

- `role`: `PENDING`, `STAFF`, `ADMIN`
- `department`: `MEDICAL`, `DEV`, `RESEARCH`

Notion 요구사항의 표현인 `사내 의료인`, `개발진`, `의료 실무진`, `연구진`은 현재 코드 기준으로 아래처럼 해석한다.

| 요구사항 표현 | 현재 코드 매핑 |
| --- | --- |
| 로그인 된 사내 개발진, 의료 실무진, 연구진 | `role in {STAFF, ADMIN}` 이고 `PENDING` 아님 |
| 사내 의료인 역할 | `department == MEDICAL` 이고 `role in {STAFF, ADMIN}` |

### 권한 매트릭스

| API | 허용 대상 |
| --- | --- |
| 환자 목록/상세 조회 | `STAFF`, `ADMIN` |
| 환자 수정/삭제 | `STAFF`, `ADMIN` |
| 환자 등록 | `MEDICAL + STAFF`, `ADMIN` |
| 진료기록 등록 | `MEDICAL + STAFF`, `ADMIN` |
| 진료기록 목록/상세 조회 | `STAFF`, `ADMIN` |
| 전체 API | `PENDING` 접근 불가 |

### 구현 원칙

- JWT 해석은 각 router에서 직접 하지 않는다.
- 공통 dependency로 권한을 검사한다.
- 최소 아래 함수는 공통으로 제공한다.
  - `get_current_user()`
  - `require_staff_or_admin()`
  - `require_medical_staff_or_admin()`

---

## 4. 공통 API 규칙

### URL 규칙

- Base URL은 `/api/v1`
- 리소스명은 복수형 사용
- 환자 리소스는 `/patients`
- 진료기록 리소스는 환자 하위 경로인 `/patients/{patient_id}/medical-records`

### ID 규칙

- 환자 ID와 진료기록 ID는 정수형 사용
- Swagger 테스트 편의와 현재 모델 구조를 고려해 `int` 기반으로 통일

### 시간 규칙

- DB 저장은 UTC 기준
- API 응답은 ISO 8601 문자열
- 예시: `2026-07-21T07:00:00Z`

### 목록 규칙

- 페이지네이션은 `offset`, `limit` 방식
- 기본값: `offset=0`, `limit=20`
- 최대 `limit=100`
- 환자 목록 정렬: `created_at DESC`
- 진료기록 목록 정렬: `created_at DESC`

### 오류 응답 규칙

- 현재 프로젝트의 전역 예외 핸들러를 그대로 사용한다.
- Stage 5 API의 오류 응답은 아래 형식으로 통일한다.

```json
{
  "code": "PATIENT_NOT_FOUND",
  "message": "Patient not found"
}
```

- FastAPI 기본 `detail` 포맷은 사용하지 않는다.
- Stage 5 전체 API가 동일한 오류 포맷을 사용해야 한다.

### 공통 에러 메시지 상수

```python
PATIENT_NOT_FOUND = "Patient not found"
MEDICAL_RECORD_NOT_FOUND = "Medical record not found"
DUPLICATE_CHART_NUMBER = "Chart number already exists"
INVALID_XRAY_FILE = "Only JPG, JPEG and PNG files are allowed"
XRAY_FILE_TOO_LARGE = "X-Ray image must be 10MB or smaller"
EMPTY_UPDATE_PAYLOAD = "At least one field is required"
```

---

## 5. 데이터 모델 계약

현재 코드베이스에는 이미 아래 모델 파일이 있다.

- `app/models/patients.py`
- `app/models/medical_records.py`
- `app/models/xray_image.py`

Stage 5에서는 기존 파일명을 유지한다.

### Patients

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `id` | int | PK |
| `name` | varchar(50) | required |
| `age` | int | required |
| `gender` | enum(`M`, `F`) | required |
| `phone` | varchar(20) | required |
| `created_at` | datetime | required |
| `updated_at` | datetime | nullable |

### MedicalRecord

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `id` | int | PK |
| `patient_id` | int | FK, required |
| `chart_number` | varchar(50) | required, unique |
| `symptoms` | text | required |
| `created_at` | datetime | required |
| `updated_at` | datetime | nullable |

### XrayImage

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `id` | int | PK |
| `record_id` | int | FK, required |
| `uploader_id` | int | nullable |
| `image_url` | varchar | required |
| `shooting_datetime` | datetime | required |
| `created_at` | datetime | required |

### 관계 규칙

- `Patient 1 : N MedicalRecord`
- `MedicalRecord 1 : N XrayImage`
- 이번 Stage에서는 진료기록 등록 시 X-Ray 이미지는 1개만 업로드 받는다.
- 기존 `xray_images` 테이블 구조는 유지하되, API 레벨에서는 단일 이미지 업로드 계약으로 고정한다.

### 삭제 규칙

- 환자 삭제 시 연결된 진료기록도 삭제한다.
- 연결된 X-Ray 파일도 함께 삭제한다.
- DB cascade와 서비스 계층 파일 삭제를 함께 사용한다.

### 설계 선택 사항

아래는 요구사항 자체가 아니라 팀 설계 선택이다.

- `chart_number`는 시스템 전체에서 unique
- 파일 경로는 DB에 상대 경로만 저장
- 응답에는 접근 가능한 URL을 조합해 반환

---

## 6. 입력 검증 규칙

### Patient

| 필드 | 규칙 |
| --- | --- |
| `name` | 앞뒤 공백 제거 후 1~50자 |
| `age` | 0~150 |
| `gender` | `M`, `F`만 허용 |
| `phone` | 숫자와 하이픈 허용, 저장 시 숫자만 유지 |

### Medical Record

| 필드 | 규칙 |
| --- | --- |
| `chart_number` | 앞뒤 공백 제거 후 1~50자 |
| `symptoms` | 1~5000자 |
| `xray` | `jpg`, `jpeg`, `png`만 허용 |
| `xray` 크기 | 최대 10MB |

### 수정 API 규칙

- 환자 수정 API는 `name`, `phone`만 허용한다.
- partial update로 구현한다.
- 수정 요청에 두 필드가 모두 없으면 `422 Unprocessable Entity`

### 연락처 정규화 규칙

입력:

```text
010-1234-5678
```

저장:

```text
01012345678
```

응답:

```text
01012345678
```

### 공통 유틸 함수

- `normalize_phone()`
- `validate_xray_file_extension()`
- `validate_xray_file_size()`

---

## 7. 요청 및 응답 명세

### 7.1 환자 등록

`POST /api/v1/patients`

```json
{
  "name": "홍길동",
  "age": 35,
  "gender": "M",
  "phone": "01012345678"
}
```

성공 응답:

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 35,
  "gender": "M",
  "phone": "01012345678",
  "created_at": "2026-07-21T07:00:00Z",
  "updated_at": "2026-07-21T07:00:00Z"
}
```

### 7.2 환자 목록 조회

`GET /api/v1/patients?name=김&gender=F&min_age=20&max_age=40&offset=0&limit=20`

성공 응답:

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
      "updated_at": "2026-07-21T07:00:00Z"
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 20
}
```

### 7.3 환자 상세 조회

`GET /api/v1/patients/{patient_id}`

응답 필드:

- `id`
- `name`
- `age`
- `gender`
- `phone`
- `created_at`
- `updated_at`

### 7.4 환자 수정

`PATCH /api/v1/patients/{patient_id}`

```json
{
  "name": "홍길순",
  "phone": "010-9999-0000"
}
```

### 7.5 환자 삭제

`DELETE /api/v1/patients/{patient_id}`

- 성공 시 `204 No Content`
- 환자, 연관 진료기록, 연관 X-Ray 파일까지 삭제

### 7.6 진료기록 등록

`POST /api/v1/patients/{patient_id}/medical-records`

- `multipart/form-data`
- `patient_id`는 URL path로만 받는다.
- form-data에 `patient_id`를 중복해서 받지 않는다.

폼 필드:

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| `chart_number` | text | Y |
| `symptoms` | text | Y |
| `xray` | file | Y |

응답 예시:

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

### 7.7 진료기록 목록 조회

`GET /api/v1/patients/{patient_id}/medical-records?offset=0&limit=20`

성공 응답:

```json
{
  "items": [
    {
      "id": 1,
      "chart_number": "XR-2026-0001",
      "symptoms": "기침 및 흉통",
      "created_at": "2026-07-21T07:00:00Z"
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 20
}
```

추가 규칙:

- 목록의 `symptoms`는 100자를 초과하면 API에서 `앞 100자...` 형태로 잘라서 반환한다.
- 원문은 DB에 그대로 저장한다.

### 7.8 진료기록 상세 조회

`GET /api/v1/patients/{patient_id}/medical-records/{record_id}`

성공 응답:

```json
{
  "id": 1,
  "patient_id": 12,
  "chart_number": "XR-2026-0001",
  "symptoms": "기침 및 흉통",
  "xray_url": "/uploads/xrays/12/550e8400-e29b-41d4-a716-446655440000.png",
  "created_at": "2026-07-21T07:00:00Z"
}
```

---

## 8. 상태 코드 표준

| 상황 | 상태 코드 |
| --- | --- |
| 등록 성공 | `201 Created` |
| 조회/수정 성공 | `200 OK` |
| 삭제 성공 | `204 No Content` |
| 인증 실패 | `401 Unauthorized` |
| 권한 부족 | `403 Forbidden` |
| 대상 없음 | `404 Not Found` |
| 차트 번호 중복 | `409 Conflict` |
| 입력값 또는 파일 오류 | `422 Unprocessable Entity` |
| 파일 저장 실패 | `500 Internal Server Error` |

---

## 9. X-Ray 파일 저장 규칙

### 저장 위치

```text
uploads/xrays/{patient_id}/{uuid}.{extension}
```

예시:

```text
uploads/xrays/12/550e8400-e29b-41d4-a716-446655440000.png
```

### DB 저장값

- DB에는 절대 경로가 아니라 상대 경로만 저장한다.

```text
xrays/12/550e8400-e29b-41d4-a716-446655440000.png
```

### 응답 노출값

```json
{
  "xray_url": "/uploads/xrays/12/550e8400-e29b-41d4-a716-446655440000.png"
}
```

### 파일 처리 순서

1. 환자 존재 확인
2. 파일 확장자, MIME, 크기 검증
3. UUID 파일명 생성
4. 로컬 저장소에 파일 저장
5. DB 레코드 생성
6. DB 실패 시 저장된 파일 삭제

### 환자 삭제 처리 순서

1. 삭제 대상 X-Ray 파일 경로 목록 조회
2. DB transaction 안에서 환자와 연관 데이터 삭제
3. commit 성공 후 실제 파일 삭제
4. 파일이 이미 없어도 환자 삭제 자체는 성공 처리

### 공통 파일 함수

- `save_xray_file()`
- `delete_xray_file()`

---

## 10. 공통 구현 담당 범위

공통 PR에서 먼저 만들거나 정리할 대상:

- `app/models/patients.py`
- `app/models/medical_records.py`
- `app/models/xray_image.py`
- `app/schemas/patient.py`
- `app/schemas/medical_record.py`
- `app/schemas/common.py`
- `app/apis/dependencies.py` 또는 기존 dependency 위치에 맞는 공통 파일
- `app/services/file_storage.py`
- `app/utils/validators.py`

공통으로 제공해야 하는 함수:

- `get_patient_or_404()`
- `get_medical_record_or_404()`
- `require_staff_or_admin()`
- `require_medical_staff_or_admin()`
- `normalize_phone()`
- `save_xray_file()`
- `delete_xray_file()`

공통 PR 병합 전 규칙:

- 팀원은 공통 모델, 스키마, dependency를 각자 브랜치에서 임의로 수정하지 않는다.
- 변경이 필요하면 공통 PR에 먼저 반영하거나 팀장과 합의 후 수정한다.

### 이번 공통 PR에서 이미 반영한 내용

- 환자/진료기록 공통 dependency 추가
- 환자/진료기록 스키마 추가
- X-Ray 파일 저장 서비스 추가
- 전화번호/X-Ray 검증 유틸 추가
- 환자 삭제 cascade에 맞춘 모델 보정
- `/uploads` 정적 파일 경로 마운트
- Stage 5용 예외 클래스 추가
- Alembic 마이그레이션 추가

---

## 11. 추천 작업 분담

| 담당 | 범위 |
| --- | --- |
| 팀장 | 공통 코드, `POST /patients`, `GET /patients`, 설계 문서 정리 |
| 팀원 1 | `GET /patients/{patient_id}`, `PATCH /patients/{patient_id}`, `DELETE /patients/{patient_id}` |
| 팀원 2 | `POST /patients/{patient_id}/medical-records`, 파일 저장 처리 |
| 팀원 3 | `GET /patients/{patient_id}/medical-records`, `GET /patients/{patient_id}/medical-records/{record_id}`, 응답 형식 통일 |

각 담당 공통 요구:

- Swagger에서 직접 테스트 가능해야 한다.
- 각자 구현 API에 대해 최소 정상, `401`, `403`, `404`, `422` 케이스를 확인한다.
- 필요한 경우 문서 예시도 함께 수정한다.

---

## 12. 에이전트 작업 지시용 요약

아래 블록은 팀원이 에이전트에게 그대로 전달할 수 있는 요약이다.

```text
Stage 5 환자 관리 및 진료기록 API 작업이다.

고정 규칙:
- Base URL은 /api/v1
- 필수 API는 환자 5개, 진료기록 3개다.
- 진료기록 수정/삭제는 이번 Stage 범위에서 제외한다.
- 환자 목록 필터는 name, gender, min_age, max_age, offset, limit를 사용한다.
- 목록 페이지네이션은 offset/limit 방식이다.
- 환자 수정은 name, phone만 허용한다.
- phone은 입력 시 하이픈 허용, 저장은 숫자만 유지한다.
- chart_number는 전역 unique다.
- 진료기록 등록은 multipart/form-data를 사용한다.
- X-Ray는 jpg, jpeg, png만 허용하고 최대 10MB다.
- 파일은 uploads/xrays/{patient_id}/{uuid}.{ext}에 저장하고 DB에는 상대 경로만 저장한다.
- 환자 삭제 시 연관 진료기록과 X-Ray 파일도 함께 삭제한다.
- 시간은 UTC 저장, 응답은 ISO 8601 형식이다.

권한 규칙:
- PENDING은 전체 API 접근 불가
- 조회, 환자 수정, 환자 삭제는 STAFF 또는 ADMIN 허용
- 환자 등록, 진료기록 등록은 MEDICAL 부서의 STAFF 또는 ADMIN 허용

응답 규칙:
- 환자/진료기록 단건 응답은 리소스 객체 그대로 반환한다.
- 목록 응답은 items, total, offset, limit 형태다.
- 오류 응답은 detail 필드를 사용한다.

공통 함수:
- get_patient_or_404()
- get_medical_record_or_404()
- require_staff_or_admin()
- require_medical_staff_or_admin()
- normalize_phone()
- save_xray_file()
- delete_xray_file()

현재 문서:
- docs/5일차_환자관리_API_설계.md
```

---

## 13. 팀 공유 메시지 초안

```text
Stage 5는 병합 충돌을 줄이기 위해 공통 규칙부터 먼저 고정하고 진행하겠습니다.

필수 범위는 환자 5개 API와 진료기록 3개 API입니다.
POST /patients
GET /patients
GET /patients/{patient_id}
PATCH /patients/{patient_id}
DELETE /patients/{patient_id}
POST /patients/{patient_id}/medical-records
GET /patients/{patient_id}/medical-records
GET /patients/{patient_id}/medical-records/{record_id}

진료기록 수정/삭제는 이번 Stage 필수 범위에서 제외합니다.

권한은 현재 코드 구조에 맞춰 이렇게 해석하겠습니다.
- PENDING은 전체 API 접근 불가
- 조회, 환자 수정, 환자 삭제는 STAFF 또는 ADMIN 허용
- 환자 등록, 진료기록 등록은 MEDICAL 부서의 STAFF 또는 ADMIN 허용

공통 규칙은 다음으로 통일합니다.
- ID는 int 기반
- 시간은 UTC 저장, 응답은 ISO 8601
- 환자 목록과 진료기록 목록은 offset/limit 페이지네이션
- 환자 수정은 name, phone만 partial update
- phone은 하이픈 입력 허용, 저장은 숫자만 유지
- 진료기록 등록은 multipart/form-data
- X-Ray는 JPG/JPEG/PNG, 최대 10MB
- 파일은 uploads/xrays/{patient_id}/{uuid}.{확장자}에 저장하고 DB에는 상대 경로만 저장
- chart_number는 전역 unique
- 환자 삭제 시 연관 진료기록과 X-Ray 파일까지 함께 삭제

먼저 공통 모델, 스키마, 권한 dependency, 파일 저장 코드를 공통 PR로 병합한 뒤 각자 작업 브랜치를 따겠습니다.
공통 파일은 합의 없이 직접 수정하지 말고, 변경 필요 시 먼저 공유해주세요.

각자 담당 API는 Swagger 기준으로 정상/401/403/404/422까지 확인하고, docs/5일차_환자관리_API_설계.md도 함께 참고해서 구현 부탁드립니다.
```
