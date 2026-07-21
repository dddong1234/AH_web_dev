# 진료기록 상세 조회 API 명세서

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자별 진료기록 상세 조회 API |
| 요구사항 ID | `REQ-MDR-003` |
| 설명 | 특정 환자에게 속한 진료기록의 전체 증상과 흉부 X-Ray 이미지 정보를 조회한다. |
| Method | `GET` |
| Endpoint | `/api/v1/patients/{patient_id}/medical-records/{record_id}` |
| Content-Type | `application/json` |
| 인증 필요 여부 | Y |
| 허용 권한 | `STAFF`, `ADMIN` |
| 제한 권한 | `PENDING` |

---

## 2. 요청(Request)

### Headers

| Key | Value | 필수 | 설명 |
| --- | --- | --- | --- |
| `Authorization` | `Bearer {access_token}` | Y | JWT Access Token |
| `Accept` | `application/json` | N | 응답 미디어 타입 |

### Path Parameter

| 이름 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `patient_id` | integer | Y | 1 이상의 정수 | 환자 고유 ID |
| `record_id` | integer | Y | 1 이상의 정수 | 진료기록 고유 ID |

### Query Parameter

사용하지 않는다.

### Request Body

GET 요청이므로 Request Body를 사용하지 않는다.

### 요청 예시

```http
GET /api/v1/patients/12/medical-records/1 HTTP/1.1
Authorization: Bearer {access_token}
Accept: application/json
```

---

## 3. 응답(Response)

### 성공 응답

- Status Code: `200 OK`
- Content-Type: `application/json`

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

### 성공 응답 필드

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `id` | integer | Y | 진료기록 고유 ID |
| `patient_id` | integer | Y | 진료기록이 속한 환자 고유 ID |
| `chart_number` | string | Y | 진료 차트 번호 |
| `symptoms` | string | Y | 증상 전체 내용. 목록 응답과 달리 축약하지 않음 |
| `xray_url` | string | Y | 흉부 X-Ray 이미지 접근 URL |
| `created_at` | string(datetime) | Y | 진료기록 생성일시. UTC 기반 ISO 8601 형식 |

### 실패 응답

| Status Code | 오류 코드 | 발생 조건 |
| --- | --- | --- |
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | Authorization Header가 없음 |
| `401 Unauthorized` | `INVALID_ACCESS_TOKEN` | Access Token이 유효하지 않음 |
| `401 Unauthorized` | `ACCESS_TOKEN_EXPIRED` | Access Token이 만료됨 |
| `403 Forbidden` | `PERMISSION_DENIED` | `PENDING` 사용자가 접근함 |
| `404 Not Found` | `PATIENT_NOT_FOUND` | `patient_id`에 해당하는 환자가 없음 |
| `404 Not Found` | `MEDICAL_RECORD_NOT_FOUND` | 진료기록이 없거나 해당 환자에게 속하지 않음 |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | Path Parameter 검증 실패 |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | 서버 내부 오류 |

### 유효하지 않은 Access Token 응답 예시

```json
{
  "code": "INVALID_ACCESS_TOKEN",
  "message": "유효하지 않은 Access Token입니다."
}
```

### 만료된 Access Token 응답 예시

```json
{
  "code": "ACCESS_TOKEN_EXPIRED",
  "message": "Access Token이 만료되었습니다."
}
```

### 환자 없음 응답 예시

```json
{
  "code": "PATIENT_NOT_FOUND",
  "message": "Patient not found"
}
```

### 진료기록 없음 응답 예시

```json
{
  "code": "MEDICAL_RECORD_NOT_FOUND",
  "message": "Medical record not found"
}
```

---

## 4. 처리 규칙

1. 공통 Dependency로 JWT를 검증한다.
2. 현재 사용자의 권한이 `STAFF` 또는 `ADMIN`인지 확인한다.
3. `get_patient_or_404()`로 환자 존재 여부를 먼저 확인한다.
4. `patient_id`와 `record_id`를 함께 사용하여 진료기록을 조회한다.
5. `record_id`가 존재하더라도 다른 환자의 진료기록이면 `404 MEDICAL_RECORD_NOT_FOUND`를 반환한다.
6. 진료기록에 연결된 X-Ray 이미지의 상대 경로를 접근 가능한 `/uploads/...` URL로 변환해 `xray_url`로 반환한다.
7. `symptoms`는 축약하지 않고 전체 내용을 반환한다.
8. 처리 시간은 정상적인 운영 환경에서 3초 이내를 목표로 한다.

---

## 5. Swagger 테스트 항목

| 테스트 | 입력/조건 | 기대 결과 |
| --- | --- | --- |
| 정상 조회 | STAFF 또는 ADMIN Token, 올바른 환자 및 진료기록 ID | `200 OK`, 전체 진료기록 반환 |
| 인증 누락 | Authorization Header 없음 | `401 Unauthorized` |
| 권한 부족 | PENDING Token | `403 Forbidden` |
| 환자 없음 | 존재하지 않는 `patient_id` | `404 PATIENT_NOT_FOUND` |
| 진료기록 없음 | 존재하지 않는 `record_id` | `404 MEDICAL_RECORD_NOT_FOUND` |
| 소유 관계 불일치 | 다른 환자에게 속한 `record_id` | `404 MEDICAL_RECORD_NOT_FOUND` |
| 잘못된 ID | 0 이하의 `patient_id` 또는 `record_id` | `422 VALIDATION_ERROR` |

---

## 6. 비고

- DB에는 X-Ray 이미지의 상대 경로만 저장하고, 응답에는 접근 가능한 URL을 반환한다.
- 이번 Stage에서는 진료기록 수정 및 삭제 API를 구현하지 않는다.
- 오류 응답은 프로젝트 전역 예외 처리 규칙인 `{ "code": "...", "message": "..." }` 형식을 사용한다.