# 로그인·인증 API 명세

> URL 작성 방식, 공통 응답 구조, HTTP 상태 코드, 토큰 만료 시간 및 오류 형식은  
> [공통 규칙](./00_conventions.md)을 따른다.

## 1. 개요

이 문서는 로그인, Access Token 재발급, 로그아웃 API를 정의한다.

### 관련 요구사항

| 요구사항 ID | 내용 |
|---|---|
| `REQ-USER-002` | 가입한 사용자는 이메일과 비밀번호로 로그인할 수 있어야 한다. |
| `NFR-USER-001` | 로그인 시 JWT를 발급하고 API 인가에 사용한다. |
| `REQ-USER-003` | 로그인 사용자는 로그아웃할 수 있어야 한다. |

### API 목록

| 기능 | Method | URL | 인증 |
|---|---|---|---|
| 로그인 | `POST` | `/api/v1/auth/login` | 불필요 |
| Access Token 재발급 | `POST` | `/api/v1/auth/refresh` | Refresh Token |
| 로그아웃 | `POST` | `/api/v1/auth/logout` | Access Token |

---

# 2. 로그인

## 2.1 기본 정보

| 항목 | 내용 |
|---|---|
| API 이름 | 로그인 |
| Method | `POST` |
| URL | `/api/v1/auth/login` |
| 인증 필요 여부 | 아니요 |
| 설명 | 이메일과 비밀번호를 검증하고 JWT를 발급한다. |

---

## 2.2 Request Body

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `email` | string | 예 | 회원가입에 사용한 이메일 |
| `password` | string | 예 | 회원가입에 사용한 비밀번호 |

### 요청 예시

```json
{
  "email": "user@example.com",
  "password": "Password123!"
}
```

### 입력값 검증

- `email`은 올바른 이메일 형식이어야 한다.
- 이메일 앞뒤 공백을 제거한다.
- 이메일을 소문자로 변환한 후 사용자를 조회한다.
- `password`는 빈 문자열일 수 없다.
- 이메일 또는 비밀번호 중 어떤 값이 틀렸는지 외부에 노출하지 않는다.

---

## 2.3 성공 응답

- Status Code: `200 OK`
- Access Token은 응답 본문으로 전달한다.
- Refresh Token은 `HttpOnly` 쿠키로 전달한다.

```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### Response Field

| 필드 | 타입 | 설명 |
|---|---|---|
| `access_token` | string | API 인증에 사용하는 Access Token |
| `token_type` | string | 토큰 인증 방식으로 항상 `bearer` |
| `expires_in` | integer | Access Token 만료 시간(초) |

### Refresh Token 쿠키 예시

```text
Set-Cookie: refresh_token={token}; HttpOnly; Path=/api/v1/auth; Max-Age=604800; SameSite=Lax
```

운영 환경에서는 쿠키에 `Secure` 속성을 추가한다.

---

## 2.4 실패 응답

| Status Code | 오류 코드 | 발생 조건 |
|---:|---|---|
| `401 Unauthorized` | `INVALID_CREDENTIALS` | 이메일 또는 비밀번호가 일치하지 않음 |
| `403 Forbidden` | `INACTIVE_USER` | 비활성화된 계정 |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | 이메일 형식 또는 필수 입력값 오류 |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | 서버 내부 오류 |

### 이메일 또는 비밀번호 불일치

```json
{
  "code": "INVALID_CREDENTIALS",
  "message": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

### 비활성화된 계정

```json
{
  "code": "INACTIVE_USER",
  "message": "비활성화된 계정입니다."
}
```

---

## 2.5 처리 순서

1. 이메일과 비밀번호의 입력 형식을 검증한다.
2. 이메일을 소문자로 정규화한다.
3. 이메일에 해당하는 사용자를 조회한다.
4. 입력한 비밀번호와 저장된 비밀번호 해시를 비교한다.
5. 계정 활성화 여부를 확인한다.
6. 30분 동안 유효한 Access Token을 생성한다.
7. 7일 동안 유효한 Refresh Token을 생성한다.
8. Refresh Token을 `HttpOnly` 쿠키로 설정한다.
9. Access Token을 응답 본문으로 반환한다.

---

# 3. Access Token 재발급

## 3.1 기본 정보

| 항목 | 내용 |
|---|---|
| API 이름 | Access Token 재발급 |
| Method | `POST` |
| URL | `/api/v1/auth/refresh` |
| 인증 필요 여부 | Refresh Token 필요 |
| 설명 | Refresh Token을 검증하고 새로운 Access Token을 발급한다. |

---

## 3.2 Request

Request Body는 사용하지 않는다.

Refresh Token은 `refresh_token` 쿠키로 전달한다.

```text
Cookie: refresh_token={refresh_token}
```

Refresh Token을 Request Body 또는 Query Parameter로 전달하는 방식은 허용하지 않는다.

---

## 3.3 성공 응답

- Status Code: `200 OK`

```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### Response Field

| 필드 | 타입 | 설명 |
|---|---|---|
| `access_token` | string | 새로 발급된 Access Token |
| `token_type` | string | 토큰 인증 방식으로 항상 `bearer` |
| `expires_in` | integer | Access Token 만료 시간(초) |

---

## 3.4 실패 응답

| Status Code | 오류 코드 | 발생 조건 |
|---:|---|---|
| `401 Unauthorized` | `REFRESH_TOKEN_REQUIRED` | Refresh Token 쿠키가 없음 |
| `401 Unauthorized` | `INVALID_REFRESH_TOKEN` | 토큰 형식, 서명 또는 용도가 올바르지 않음 |
| `401 Unauthorized` | `REFRESH_TOKEN_EXPIRED` | Refresh Token이 만료됨 |
| `401 Unauthorized` | `REFRESH_TOKEN_REVOKED` | 로그아웃 등으로 폐기된 토큰 |
| `401 Unauthorized` | `USER_NOT_FOUND` | 토큰에 해당하는 사용자가 없음 |
| `403 Forbidden` | `INACTIVE_USER` | 비활성화된 계정 |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | 서버 내부 오류 |

### Refresh Token 쿠키 없음

```json
{
  "code": "REFRESH_TOKEN_REQUIRED",
  "message": "Refresh Token이 필요합니다."
}
```

### Refresh Token 만료

```json
{
  "code": "REFRESH_TOKEN_EXPIRED",
  "message": "로그인이 만료되었습니다. 다시 로그인해 주세요."
}
```

### 폐기된 Refresh Token

```json
{
  "code": "REFRESH_TOKEN_REVOKED",
  "message": "사용할 수 없는 Refresh Token입니다."
}
```

---

## 3.5 처리 순서

1. `refresh_token` 쿠키가 존재하는지 확인한다.
2. Refresh Token의 서명과 만료 시간을 검증한다.
3. Access Token이 아닌 Refresh Token인지 확인한다.
4. 로그아웃 등으로 폐기된 토큰인지 확인한다.
5. 토큰의 `user_id`로 사용자를 조회한다.
6. 계정 활성화 여부를 확인한다.
7. 새로운 Access Token을 생성한다.
8. 새로운 Access Token을 응답 본문으로 반환한다.

---

# 4. 로그아웃

## 4.1 기본 정보

| 항목 | 내용 |
|---|---|
| API 이름 | 로그아웃 |
| Method | `POST` |
| URL | `/api/v1/auth/logout` |
| 인증 필요 여부 | 예 |
| 필요 권한 | 로그인 사용자 |
| 설명 | Refresh Token을 폐기하고 해당 쿠키를 삭제한다. |

---

## 4.2 Request Header

Access Token은 Authorization 헤더로 전달한다.

```text
Authorization: Bearer {access_token}
```

Refresh Token은 쿠키로 함께 전달한다.

```text
Cookie: refresh_token={refresh_token}
```

Request Body는 사용하지 않는다.

---

## 4.3 성공 응답

- Status Code: `204 No Content`
- Response Body 없음
- `refresh_token` 쿠키 삭제

### 쿠키 삭제 예시

```text
Set-Cookie: refresh_token=; HttpOnly; Path=/api/v1/auth; Max-Age=0; SameSite=Lax
```

Refresh Token 쿠키가 이미 없더라도 Access Token이 유효하면 로그아웃에 성공한 것으로 처리한다.

---

## 4.4 실패 응답

| Status Code | 오류 코드 | 발생 조건 |
|---:|---|---|
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | Access Token이 없음 |
| `401 Unauthorized` | `INVALID_ACCESS_TOKEN` | Access Token의 형식 또는 서명이 올바르지 않음 |
| `401 Unauthorized` | `ACCESS_TOKEN_EXPIRED` | Access Token이 만료됨 |
| `401 Unauthorized` | `USER_NOT_FOUND` | 토큰에 해당하는 사용자가 없음 |
| `403 Forbidden` | `INACTIVE_USER` | 비활성화된 계정 |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | 서버 내부 오류 |

### Access Token이 없는 경우

```json
{
  "code": "AUTHENTICATION_REQUIRED",
  "message": "로그인이 필요합니다."
}
```

### Access Token이 만료된 경우

```json
{
  "code": "ACCESS_TOKEN_EXPIRED",
  "message": "Access Token이 만료되었습니다."
}
```

---

## 4.5 처리 순서

1. Authorization 헤더에서 Access Token을 가져온다.
2. Access Token의 서명과 만료 시간을 검증한다.
3. 토큰의 `user_id`로 사용자를 조회한다.
4. Refresh Token 쿠키가 있으면 서버에서 해당 토큰을 폐기한다.
5. `refresh_token` 쿠키를 삭제한다.
6. `204 No Content`를 반환한다.

---

# 5. JWT 저장 정보

JWT에는 개인정보나 권한 정보를 저장하지 않는다.

사용자 식별 정보는 `user_id`만 포함한다. 토큰 검증을 위해 다음 관리 정보를 추가할 수 있다.

| 필드 | 설명 |
|---|---|
| `user_id` | 사용자 고유 ID |
| `type` | `access` 또는 `refresh` |
| `iat` | 토큰 발급 시각 |
| `exp` | 토큰 만료 시각 |

이메일, 이름, 부서, 성별, 휴대폰 번호 및 권한은 JWT에 포함하지 않는다.

### Access Token payload 예시

```json
{
  "user_id": 1,
  "type": "access",
  "iat": 1784188800,
  "exp": 1784190600
}
```

### Refresh Token payload 예시

```json
{
  "user_id": 1,
  "type": "refresh",
  "iat": 1784188800,
  "exp": 1784793600
}
```

---

# 6. 보안 규칙

- 비밀번호 원문을 Database에 저장하지 않는다.
- 비밀번호 검증에는 Argon2 해시를 사용한다.
- 비밀번호와 JWT 전체 값을 로그에 기록하지 않는다.
- JWT Secret Key는 환경변수로 관리한다.
- 로그인 실패 시 이메일 존재 여부를 노출하지 않는다.
- Access Token과 Refresh Token의 용도를 구분한다.
- Refresh Token을 일반 API 인증에 사용할 수 없도록 한다.
- 로그아웃 시 쿠키 삭제와 서버 측 토큰 폐기를 함께 수행한다.
- 운영 환경에서는 Refresh Token 쿠키에 `Secure` 속성을 적용한다.
- 모든 인증 API는 3초 이내에 응답해야 한다.

---

