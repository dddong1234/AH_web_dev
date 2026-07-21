# 환자 목록 조회 API 명세

> Stage 5 환자 관리 API 공통 규칙은 [5일차_환자관리_API_설계.md](./5일차_환자관리_API_설계.md)를 따른다.

## 1. 기본 정보

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 목록 조회 |
| Method | `GET` |
| URL | `/api/v1/patients` |
| 인증 필요 여부 | 예 |
| 설명 | 로그인된 내부 사용자가 환자 목록을 조회한다. 이름 검색, 성별 필터, 나이 범위 필터, 페이지네이션을 지원한다. |

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

### Query Parameters

| 필드 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `name` | string | N | 없음 | 이름 부분 검색 |
| `gender` | string | N | 없음 | `M`, `F` 필터 |
| `min_age` | integer | N | 없음 | 최소 나이 |
| `max_age` | integer | N | 없음 | 최대 나이 |
| `offset` | integer | N | `0` | 조회 시작 위치 |
| `limit` | integer | N | `20` | 조회 개수 |

### 검증 규칙

- `gender`는 `M`, `F`만 허용
- `min_age`, `max_age`는 0 이상 150 이하
- `offset`은 0 이상
- `limit`은 1 이상 100 이하
- `min_age > max_age` 조합은 허용하지 않는다

### 요청 예시

```text
GET /api/v1/patients?name=김&gender=F&min_age=20&max_age=40&offset=0&limit=20
```

## 4. 정렬 규칙

- 기본 정렬: `created_at DESC`

## 5. Response

### 성공

- Status Code: `200 OK`

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

### 응답 필드

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `items` | array | 환자 목록 |
| `items[].id` | integer | 환자 ID |
| `items[].name` | string | 환자 이름 |
| `items[].age` | integer | 환자 나이 |
| `items[].gender` | string | 환자 성별 |
| `items[].phone` | string | 연락처 |
| `items[].created_at` | string | 생성 일시 |
| `items[].updated_at` | string or null | 수정 일시 |
| `total` | integer | 조건에 맞는 전체 건수 |
| `offset` | integer | 요청 offset |
| `limit` | integer | 요청 limit |

## 6. 오류 응답

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

## 7. 구현 메모

- 이름 검색은 부분 일치 기준으로 처리한다.
- `total`은 페이지네이션 적용 전 전체 개수를 반환한다.
- 응답은 `items`, `total`, `offset`, `limit` 형식으로 고정한다.
