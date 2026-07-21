# 환자 정보 등록 API 명세

> Stage 5 환자 관리 API 공통 규칙은 [5일차_환자관리_API_설계.md](./5일차_환자관리_API_설계.md)를 따른다.

## 1. 기본 정보

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 등록 |
| Method | `POST` |
| URL | `/api/v1/patients` |
| 인증 필요 여부 | 예 |
| 설명 | 의료진 권한을 가진 사용자가 환자 정보를 등록한다. |

## 2. 권한

- `MEDICAL` 부서의 `STAFF`
- `ADMIN`
- `PENDING` 접근 불가

적용 dependency:

- `require_medical_staff_or_admin()`

## 3. Request

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| `Authorization` | `Bearer {access_token}` | JWT Access Token |
| `Content-Type` | `application/json` | JSON 요청 |

### Request Body

```json
{
  "name": "홍길동",
  "age": 35,
  "gender": "M",
  "phone": "010-1234-5678"
}
```

### Body 필드

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `name` | string | Y | 환자 이름 |
| `age` | integer | Y | 환자 나이 |
| `gender` | string | Y | 성별, `M` 또는 `F` |
| `phone` | string | Y | 연락처, 하이픈 입력 허용 |

### 입력값 검증

- `name`
  - 앞뒤 공백 제거
  - 1자 이상 50자 이하
- `age`
  - 0 이상 150 이하
- `gender`
  - `M`, `F`만 허용
- `phone`
  - 숫자와 하이픈 입력 허용
  - 저장 시 숫자만 유지
  - `01012345678` 형식으로 정규화

## 4. Response

### 성공

- Status Code: `201 Created`

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
| `id` | integer | 생성된 환자 ID |
| `name` | string | 환자 이름 |
| `age` | integer | 환자 나이 |
| `gender` | string | 환자 성별 |
| `phone` | string | 정규화된 연락처 |
| `created_at` | string | 생성 일시, ISO 8601 |
| `updated_at` | string or null | 수정 일시, 없으면 `null` |

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

### 422 Unprocessable Entity

```json
{
  "code": "VALIDATION_ERROR",
  "message": "요청 데이터 유효성 검증에 실패했습니다."
}
```

## 6. 구현 메모

- 전화번호는 `normalize_phone()`로 정규화한다.
- `Patients` 엔티티 생성 후 저장한다.
- 응답은 단건 리소스 객체 그대로 반환한다.
