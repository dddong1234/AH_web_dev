# 진료기록 목록 조회 API 명세서

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자별 진료기록 목록 조회 API |
| 요구사항 ID | `REQ-MDR-002` |
| 설명 | 특정 환자의 진료기록을 최신 생성순으로 조회한다. |
| Method | `GET` |
| Endpoint | `/api/v1/patients/{patient_id}/medical-records` |
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
| `patient_id` | integer | Y | 1 이상의 정수 | 진료기록을 조회할 환자의 고유 ID |

### Query Parameter

| 이름 | 타입 | 필수 | 기본값 | 제약 | 설명 |
| --- | --- | --- | --- | --- | --- |
| `offset` | integer | N | `0` | 0 이상 | 건너뛸 진료기록 수 |
| `limit` | integer | N | `20` | 1 이상 100 이하 | 한 번에 조회할 최대 진료기록 수 |

### Request Body

GET 요청이므로 Request Body를 사용하지 않는다.

### 요청 예시

```http
GET /api/v1/patients/12/medical-records?offset=0&limit=20 HTTP/1.1
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

### 성공 응답 필드

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `items` | array | Y | 진료기록 목록. 조회 결과가 없으면 빈 배열 |
| `items[].id` | integer | Y | 진료기록 고유 ID |
| `items[].chart_number` | string | Y | 진료 차트 번호 |
| `items[].symptoms` | string | Y | 증상 요약. 원문이 100자를 초과하면 앞 100자 뒤에 `...`을 붙여 반환 |
| `items[].created_at` | string(datetime) | Y | 진료기록 생성일시. UTC 기반 ISO 8601 형식 |
| `total` | integer | Y | 해당 환자의 전체 진료기록 수 |
| `offset` | integer | Y | 요청에 적용된 offset |
| `limit` | integer | Y | 요청에 적용된 limit |

### 빈 목록 응답

환자는 존재하지만 진료기록이 없는 경우에도 `200 OK`를 반환한다.

```json
{
  "items": [],
  "total": 0,
  "offset": 0,
  "limit": 20
}
```

### 실패 응답

| Status Code | 오류 코드 | 발생 조건 |
| --- | --- | --- |
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | Authorization Header가 없음 |
| `401 Unauthorized` | `INVALID_ACCESS_TOKEN` | Access Token이 유효하지 않음 |
| `401 Unauthorized` | `ACCESS_TOKEN_EXPIRED` | Access Token이 만료됨 |
| `403 Forbidden` | `PERMISSION_DENIED` | `PENDING` 사용자가 접근함 |
| `404 Not Found` | `PATIENT_NOT_FOUND` | `patient_id`에 해당하는 환자가 없음 |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | Path 또는 Query Parameter 검증 실패 |
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

### 404 응답 예시

```json
{
  "code": "PATIENT_NOT_FOUND",
  "message": "Patient not found"
}
```

### 422 응답 예시

```json
{
  "code": "VALIDATION_ERROR",
  "message": "요청 데이터 유효성 검증에 실패했습니다."
}
```

---

## 4. 처리 규칙

1. 공통 Dependency로 JWT를 검증한다.
2. 현재 사용자의 권한이 `STAFF` 또는 `ADMIN`인지 확인한다.
3. `get_patient_or_404()`로 환자 존재 여부를 확인한다.
4. 해당 환자의 진료기록만 `created_at DESC` 순서로 조회한다.
5. `offset`, `limit`을 적용하고 필터 적용 전 전체 건수를 `total`로 반환한다.
6. `symptoms`가 100자를 초과하면 원문을 변경하지 않고 응답에서만 `앞 100자...` 형태로 축약한다.
7. 처리 시간은 정상적인 운영 환경에서 3초 이내를 목표로 한다.

---

## 5. Swagger 테스트 항목

| 테스트 | 입력/조건 | 기대 결과 |
| --- | --- | --- |
| 정상 조회 | STAFF 또는 ADMIN Token, 존재하는 환자 | `200 OK`, 최신순 목록 반환 |
| 빈 목록 | 진료기록이 없는 환자 | `200 OK`, `items: []` |
| 페이지네이션 | `offset=0&limit=1` | 최대 1건 반환 |
| 인증 누락 | Authorization Header 없음 | `401 Unauthorized` |
| 권한 부족 | PENDING Token | `403 Forbidden` |
| 환자 없음 | 존재하지 않는 `patient_id` | `404 PATIENT_NOT_FOUND` |
| 잘못된 범위 | `offset=-1` 또는 `limit=101` | `422 VALIDATION_ERROR` |

---

## 6. 비고

- 목록에서는 X-Ray 이미지 URL을 반환하지 않는다.
- 증상 전체 내용과 X-Ray 이미지는 진료기록 상세 조회 API를 사용한다.
- 오류 응답은 프로젝트 전역 예외 처리 규칙인 `{ "code": "...", "message": "..." }` 형식을 사용한다.