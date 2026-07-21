# 환자 상세 조회 API 명세

> Stage 5 환자 관리 API 공통 규칙은 [5일차_환자관리_API_설계.md](./5일차_환자관리_API_설계.md)를 따른다.

## 1. 기본 정보

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 상세 조회 |
| Method | `GET` |
| URL | `/api/v1/patients/{patient_id}` |
| 인증 필요 여부 | 예 |
| 설명 | 로그인된 내부 사용자가 특정 환자의 상세 정보를 조회한다. |

## 2. 권한

- `STAFF`
- `ADMIN`
- `PENDING` 접근 불가

적용 dependency:

- `require_staff_or_admin()`

## 3. Request

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| `Authorization` | `Bearer {access_token}` | JWT Access Token |

### Path Parameter

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `patient_id` | integer | Y | 조회 대상 환자 ID |

### 요청 예시

```text
GET /api/v1/patients/1
```

## 4. Response

### 성공

- Status Code: `200 OK`

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

### 응답 필드

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | integer | 환자 ID |
| `name` | string | 환자 이름 |
| `age` | integer | 환자 나이 |
| `gender` | string | 환자 성별 |
| `phone` | string | 연락처 |
| `created_at` | string | 생성 일시 |
| `updated_at` | string or null | 수정 일시 |

## 5. 오류 응답

### 401 Unauthorized

```json
{
  "code": "AUTHENTICATION_REQUIRED",
  "message": "로그인이 필요합니다."
}
```

### 403 Forbidden

```json
{
  "code": "PERMISSION_DENIED",
  "message": "접근 권한이 없습니다."
}
```

### 404 Not Found

```json
{
  "code": "PATIENT_NOT_FOUND",
  "message": "Patient not found"
}
```

## 6. 구현 메모

- `get_patient_or_404()` 공통 함수를 사용한다.
- 응답은 환자 단건 리소스 객체 그대로 반환한다.
