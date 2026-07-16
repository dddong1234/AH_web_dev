# 관리자 회원 관리 API

이 문서는 관리자 권한 사용자가 회원 목록을 조회하고 회원 권한을 변경하기 위한 API를 정의한다.

## 1. 회원 목록 조회 API

### API 개요

- 요구사항 ID: `REQ-USER-004`
- Method: `GET`
- URL: `/api/v1/admin/users`
- 설명: 관리자 권한 사용자가 전체 회원을 페이지 단위로 조회한다. 이메일 또는 이름으로 검색할 수 있으며 부서별 필터를 적용할 수 있다.
- 인증 필요 여부: `Y`
- 필요 권한: `ADMIN`

---

### 요청

#### Headers

| 이름 | 값 | 필수 | 설명 |
| --- | --- | --- | --- |
| `Authorization` | `Bearer {access_token}` | 예 | 로그인 시 발급받은 Access Token |
| `Accept` | `application/json` | 아니요 | 응답 데이터 형식 |

#### Path Parameter

없음

#### Query Parameter

| 이름 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `page` | integer | 아니요 | `1` | 조회할 페이지 번호. 1 이상 |
| `size` | integer | 아니요 | `20` | 페이지당 회원 수. 1 이상 100 이하 |
| `search` | string | 아니요 | 없음 | 이메일 또는 이름 부분 일치 검색어 |
| `department` | string(enum) | 아니요 | 없음 | 부서 필터: `RESEARCH`, `MEDICAL`, `DEV` |

#### 요청 예시

```http
GET /api/v1/admin/users?page=1&size=20&search=홍길동&department=DEV
Authorization: Bearer {access_token}
```

#### Request Body

없음

---

### 성공 응답

- Status Code: `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "홍길동",
      "department": "DEV",
      "gender": "M",
      "phone_number": "01012345678",
      "role": "STAFF",
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

#### 응답 필드

##### 회원 정보

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `id` | integer | 회원 고유 ID |
| `email` | string | 회원 이메일 |
| `name` | string | 회원 이름 |
| `department` | string(enum) | 부서: `RESEARCH`, `MEDICAL`, `DEV` |
| `gender` | string(enum) | 성별: `M`, `F` |
| `phone_number` | string | 하이픈이 제거된 11자리 휴대폰 번호 |
| `role` | string(enum) | 권한: `PENDING`, `STAFF`, `ADMIN` |
| `is_active` | boolean | 계정 활성화 여부 |

##### 페이지네이션 정보

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `page` | integer | 현재 페이지 번호 |
| `size` | integer | 페이지당 회원 수 |
| `total` | integer | 조건에 일치하는 전체 회원 수 |
| `total_pages` | integer | 전체 페이지 수 |

조회 결과가 없더라도 오류로 처리하지 않고 `200 OK`와 빈 배열을 반환한다.

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 0,
    "total_pages": 0
  }
}
```

---

### 실패 응답

| Status Code | 오류 코드 | 발생 조건 |
| --- | --- | --- |
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | Authorization 헤더 또는 Access Token이 없음 |
| `401 Unauthorized` | `INVALID_TOKEN` | Access Token이 올바르지 않음 |
| `401 Unauthorized` | `ACCESS_TOKEN_EXPIRED` | Access Token이 만료됨 |
| `403 Forbidden` | `PERMISSION_DENIED` | 로그인 사용자의 권한이 `ADMIN`이 아님 |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | `page`, `size` 또는 `department` 값이 검증 규칙에 맞지 않음 |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | 서버 내부 처리 중 오류 발생 |

#### 오류 응답 예시

```json
{
  "code": "PERMISSION_DENIED",
  "message": "관리자 권한이 필요합니다."
}
```

---

### 처리 규칙

- Access Token으로 로그인 사용자를 식별한다.
- 로그인 사용자의 권한이 `ADMIN`인지 확인한다.
- `ADMIN`이 아닌 사용자의 요청에는 `403 Forbidden`을 반환한다.
- `search`가 전달되면 이메일 또는 이름에 검색어가 포함된 회원을 조회한다.
- `department`가 전달되면 해당 부서와 정확히 일치하는 회원만 조회한다.
- `search`와 `department`가 함께 전달되면 두 조건을 모두 만족하는 회원을 조회한다.
- `page`는 1 이상이어야 한다.
- `size`는 1 이상 100 이하여야 한다.
- 회원 목록에는 `password`, `hashed_password`, `refresh_token`을 포함하지 않는다.
- 목록 조회에는 페이지네이션을 적용한다.
- 정상적인 서비스 환경에서 3초 이내에 응답한다.

---

## 2. 회원 권한 변경 API

### API 개요

- 요구사항 ID: `REQ-USER-005`
- Method: `PATCH`
- URL: `/api/v1/admin/users/{user_id}/role`
- 설명: 관리자 권한 사용자가 지정한 회원의 권한을 `PENDING`, `STAFF`, `ADMIN` 중 하나로 변경한다.
- 인증 필요 여부: `Y`
- 필요 권한: `ADMIN`

---

### 요청

#### Headers

| 이름 | 값 | 필수 | 설명 |
| --- | --- | --- | --- |
| `Authorization` | `Bearer {access_token}` | 예 | 로그인 시 발급받은 Access Token |
| `Content-Type` | `application/json; charset=UTF-8` | 예 | 요청 데이터 형식과 문자 인코딩 |

#### Path Parameter

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `user_id` | integer | 예 | 권한을 변경할 회원의 고유 ID. 1 이상 |

#### Query Parameter

없음

#### Request Body

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `role` | string(enum) | 예 | 변경할 권한: `PENDING`, `STAFF`, `ADMIN` |

```json
{
  "role": "STAFF"
}
```

#### 요청 예시

```http
PATCH /api/v1/admin/users/3/role
Authorization: Bearer {access_token}
Content-Type: application/json; charset=UTF-8
```

```json
{
  "role": "STAFF"
}
```

---

### 성공 응답

- Status Code: `200 OK`

```json
{
  "data": {
    "id": 3,
    "email": "user@example.com",
    "name": "홍길동",
    "role": "STAFF"
  }
}
```

#### 응답 필드

| 이름 | 타입 | 설명 |
| --- | --- | --- |
| `id` | integer | 권한이 변경된 회원의 고유 ID |
| `email` | string | 회원 이메일 |
| `name` | string | 회원 이름 |
| `role` | string(enum) | 변경된 권한: `PENDING`, `STAFF`, `ADMIN` |

---

### 실패 응답

| Status Code | 오류 코드 | 발생 조건 |
| --- | --- | --- |
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | Authorization 헤더 또는 Access Token이 없음 |
| `401 Unauthorized` | `INVALID_TOKEN` | Access Token이 올바르지 않음 |
| `401 Unauthorized` | `ACCESS_TOKEN_EXPIRED` | Access Token이 만료됨 |
| `403 Forbidden` | `PERMISSION_DENIED` | 로그인 사용자의 권한이 `ADMIN`이 아님 |
| `404 Not Found` | `USER_NOT_FOUND` | `user_id`에 해당하는 회원이 없음 |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | `user_id`가 1 미만이거나 허용되지 않은 권한값을 요청함 |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | 서버 내부 처리 중 오류 발생 |

#### 오류 응답 예시: 관리자 권한 없음

```json
{
  "code": "PERMISSION_DENIED",
  "message": "관리자 권한이 필요합니다."
}
```

#### 오류 응답 예시: 변경 대상 회원 없음

```json
{
  "code": "USER_NOT_FOUND",
  "message": "사용자를 찾을 수 없습니다."
}
```

#### 오류 응답 예시: 잘못된 권한값

```json
{
  "code": "VALIDATION_ERROR",
  "message": "role은 PENDING, STAFF, ADMIN 중 하나여야 합니다."
}
```

---

### 처리 규칙

- Access Token으로 로그인 사용자를 식별한다.
- 로그인 사용자의 권한이 `ADMIN`인지 확인한다.
- `ADMIN`이 아닌 사용자의 요청에는 `403 Forbidden`을 반환한다.
- `user_id`에 해당하는 회원이 존재하는지 확인한다.
- 변경 가능한 권한은 `PENDING`, `STAFF`, `ADMIN`으로 제한한다.
- 대상 회원의 권한만 변경하며 다른 회원 정보는 수정하지 않는다.
- 변경 결과를 Database에 저장한 후 변경된 회원 정보를 반환한다.
- 응답에는 `password`, `hashed_password`, `refresh_token`을 포함하지 않는다.
- 정상적인 서비스 환경에서 3초 이내에 응답한다.
