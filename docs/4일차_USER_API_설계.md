# 01_signup.md - API 명세서(회원가입)

## 1. API 개요 (회원가입)

| 항목 | 내용 |
| --- | --- |
| API 이름 | 사용자 회원가입 API |
| 설명 | 사내 의료인, 개발 실무진, 연구진의 가입 신청 API |
| 엔드포인트(Endpoint) | `/api/v1/auth/signup` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |

### 본문 예시

```json
{
  "email": "user@example.com",
  "password": "Password123!",
  "name": "홍길동",
  "department": "DEV",
  "gender": "M",
  "phone_number": "01012345678"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| email | string | Y | 사용자 이메일 (소문자 정규화, 중복 불가) |
| password | string | Y | 사용자 비밀번호 (최소 8자, 영/수/특 각각 1개 이상 포함) |
| name | string | Y | 사용자 이름 (2자 이상 20자 이하) |
| department | string | Y | 부서 (Enum: RESEARCH, MEDICAL, DEV) |
| gender | string | Y | 성별 (Enum: M, F) |
| phone_number | string | Y | 휴대폰 번호 (하이픈 제외 숫자만 11자리, 중복 불가) |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| 없음 | - | N | 회원가입 API는 쿼리 파라미터를 사용하지 않음 |

---

## 3. 응답(Response)

### 성공

- 201 Created

    ```json
    {
      "data": {
        "id": 1,
        "email": "user@example.com",
        "name": "홍길동",
        "department": "DEV",
        "gender": "M",
        "phone_number": "01012345678",
        "role": "PENDING",
        "is_active": true
      }
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | data | object | 회원가입 완료 데이터 |
    | data.id | integer | 생성된 사용자 고유 ID |
    | data.email | string | 가입된 사용자 이메일 |
    | data.name | string | 사용자 이름 |
    | data.department | string | 소속 부서 |
    | data.gender | string | 성별 |
    | data.phone_number | string | 휴대폰 번호 (하이픈 제외 11자리) |
    | data.role | string | 기본 가입 권한, PENDING |
    | data.is_active | boolean | 계정 활성화 여부, true |

### 실패

- 409 Conflict

    ```json
    {
      "code": "EMAIL_ALREADY_EXISTS",
      "message": "이미 사용 중인 이메일 주소입니다."
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | code | string | 이메일 중복 오류 코드 |
    | message | string | 에러 원인 메시지 |

- 409 Conflict

    ```json
    {
      "code": "PHONE_NUMBER_ALREADY_EXISTS",
      "message": "이미 사용 중인 휴대폰 번호입니다."
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | code | string | 휴대폰 번호 중복 오류 코드 |
    | message | string | 에러 원인 메시지 |

- 422 Unprocessable Entity

    ```json
    {
      "code": "VALIDATION_ERROR",
      "message": "요청 데이터 유효성 검증에 실패했습니다."
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | code | string | 필드 값 검증 실패 오류 코드 |
    | message | string | 에러 상세 요약 메시지 |

---

## 4. 비고

- 회원가입이 완료되면 사용자의 기본 권한은 대기자(`PENDING`)로 지정된다.
- 패스워드는 해싱 알고리즘(`Argon2`)을 거쳐 데이터베이스에 안전하게 저장된다.
- 이메일 주소는 가입 전에 모두 소문자로 변환 처리(정규화)된다.
- 핸드폰 번호는 하이픈(`-`) 기호가 자동으로 삭제 처리된 뒤 저장된다.

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

# 마이페이지 API 명세서
## 1. API 개요
| 기능 | 요구사항 ID | Method | URL | 인증 | 필요 권한 |
| --- | --- | --- | --- | --- | --- |
| 마이페이지 정보 조회 | `REQ-USER-006` | `GET` | `/api/v1/users/me` | Y | 모든 로그인 사용자 |
| 마이페이지 정보 수정 | `REQ-USER-007` | `PATCH` | `/api/v1/users/me` | Y | 모든 로그인 사용자 |
| 비밀번호 변경 | `REQ-USER-008` | `PATCH` | `/api/v1/users/me/password` | Y | 모든 로그인 사용자 |

### 공동 요청 Headers
| Key | Value | 필수 | 설명 |
| --- | --- | --- | --- |
| Authorization | `Bearer {access_token}` | Y | JWT 액세스 토큰 |
| Content-Type | `application/json` | PATCH 요청 시 Y | 요청 본문 형식 |
| Accept | `application/json` | N | 응답 형식 |
- `PENDING`,`STAFF`,`ADMIN` 사용자가 이용할 수 있다.
- URL 마지막에는 슬래시를 붙이지 않는다.
- Path Parameter와 Query Parameter는 사용하지 않는다.

---
## 2. 마이페이지 정보 조회
### 기본 정보
|항목 |내용|
| --- | --- | 
|요구사항 ID |`REQ-USER-006`|
|API 이름|마이페이지 정보 조회 API|
|Method	|`GET`|
|URL|/api/v1/users/me|
|설명|로그인한 사용자가 자신의 정보를 조회한다.|
|인증 필요 여부	|Y|
|필요 권한|`PENDING`, `STAFF`, `ADMIN`|

### Path Parameter
없음
### Query Parameter
없음
### Request Body
없음
### 성공 응답
- Status Code: 200 OK
``` 
{
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "department": "DEV",
    "gender": "M",
    "phone_number": "01012345678",
    "role": "PENDING",
    "is_active": true
  }
}
```

### 응답 필드
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| data | object | 사용자 정보 |
| data.id | integer | 사용자 고유 ID |
| data.email | string | 사용자 이메일 |
| data.name | string | 사용자 이름 |
| data.department | string | 부서: `RESEARCH`, `MEDICAL`, `DEV` |
| data.gender | string | 성별: `M`, `F` |
| data.phone_number | string | 휴대폰 번호 |
| data.role | string | 권한: `PENDING`, `STAFF`, `ADMIN` |
| data.is_active | boolean | 계정 활성화 여부 |

### 실패 응답
| Status Code | 오류 코드 | 발생 조건 |
| --- | --- | --- |
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | 액세스 토큰이 없는 경우 |
| `401 Unauthorized` | `INVALID_TOKEN` | 액세스 토큰이 유효하지 않은 경우 |
| `401 Unauthorized` | `ACCESS_TOKEN_EXPIRED` | 액세스 토큰이 만료된 경우 |
| `404 Not Found` | `USER_NOT_FOUND` | 토큰에 해당하는 사용자가 없는 경우 |

### 처리 규칙
- JWT payload의 user_id를 사용해 사용자를 조회한다.
- 로그인한 본인의 정보만 반환한다.
- 비밀번호 및 리프레시 토큰은 응답에 포함하지 않는다.
- Enum 값은 영문 대문자로 반환한다.
---

## 3. 마이페이지 정보 수정
### 기본 정보
| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | `REQ-USER-007` |
| API 이름 | 마이페이지 정보 수정 API |
| Method | `PATCH` |
| URL | `/api/v1/users/me` |
| 설명 | 로그인한 사용자가 자신의 부서와 휴대폰 번호를 수정한다. |
| 인증 필요 여부 | Y |
| 필요 권한 | `PENDING`, `STAFF`, `ADMIN` |

### Path Parameter
없음
### Query Parameter
없음
### Request Body
```
{
  "department": "MEDICAL",
  "phone_number": "01098765432"
}
```
### 요청 필드
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| department | string | N | 변경할 부서: `RESEARCH`, `MEDICAL`, `DEV` |
| phone_number | string | N | 변경할 휴대폰 번호 |

`PATCH` 요청이므로 수정할 필드만 전달할 수 있습니다.
휴대폰 번호만 수정하는 예시:
```
{
  "phone_number": "01098765432"
}
```
### 성공 응답
```
Status Code: 200 OK
{
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "department": "MEDICAL",
    "gender": "M",
    "phone_number": "01098765432",
    "role": "PENDING",
    "is_active": true
  }
}
```
### 실패 응답
| Status Code | 오류 코드 | 발생 조건 |
| --- | --- | --- |
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | 액세스 토큰이 없는 경우 |
| `401 Unauthorized` | `INVALID_TOKEN` | 액세스 토큰이 유효하지 않은 경우 |
| `401 Unauthorized` | `ACCESS_TOKEN_EXPIRED` | 액세스 토큰이 만료된 경우 |
| `404 Not Found` | `USER_NOT_FOUND` | 사용자를 찾을 수 없는 경우 |
| `409 Conflict` | `PHONE_NUMBER_ALREADY_EXISTS` | 다른 사용자가 같은 휴대폰 번호를 사용하는 경우 |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | 부서 또는 휴대폰 번호 형식이 잘못된 경우 |

### 오류 응답 예시
```
{
  "code": "PHONE_NUMBER_ALREADY_EXISTS",
  "message": "이미 사용 중인 휴대폰 번호입니다."
}
```
### 처리 규칙
- department와 phone_number만 수정할 수 있다.
- 전달하지 않은 필드는 기존 값을 유지한다.
- 부서는 RESEARCH, MEDICAL, DEV 중 하나여야 한다.
- 휴대폰 번호는 숫자만 사용한다.
- 휴대폰 번호는 010으로 시작하는 11자리여야 한다.
- 하이픈이 입력되면 제거한 후 저장한다.
- 휴대폰 번호는 다른 사용자와 중복될 수 없다.
- 이메일, 이름, 성별 및 권한은 수정할 수 없다.
---

## 4. 비밀번호 변경
### 기본 정보
| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | `REQ-USER-008` |
| API 이름 | 비밀번호 변경 API |
| Method | `PATCH` |
| URL | `/api/v1/users/me/password` |
| 설명 | 기존 비밀번호를 확인한 후 새로운 비밀번호로 변경한다. |
| 인증 필요 여부 | Y |
| 필요 권한 | `PENDING`, `STAFF`, `ADMIN` |

### Path Parameter
없음
### Query Parameter
없음
### Request Body
```
{
  "current_password": "Current123!",
  "new_password": "NewPassword456!"
}
```
### 요청 필드
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| current_password | string | Y | 현재 사용 중인 비밀번호 |
| new_password | string | Y | 새로 사용할 비밀번호 |

### 성공 응답
- Status Code: 200 OK
```
{
  "data": {
    "message": "비밀번호가 변경되었습니다."
  }
}
```
### 성공 응답 필드
| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| data | object | 처리 결과 |
| data.message | string | 비밀번호 변경 완료 메시지 |

### 실패 응답
| Status Code | 오류 코드 | 발생 조건 |
| --- | --- | --- |
| `400 Bad Request` | `CURRENT_PASSWORD_MISMATCH` | 기존 비밀번호가 일치하지 않는 경우 |
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | 액세스 토큰이 없는 경우 |
| `401 Unauthorized` | `INVALID_TOKEN` | 액세스 토큰이 유효하지 않은 경우 |
| `401 Unauthorized` | `ACCESS_TOKEN_EXPIRED` | 액세스 토큰이 만료된 경우 |
| `404 Not Found` | `USER_NOT_FOUND` | 사용자를 찾을 수 없는 경우 |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | 새로운 비밀번호가 검증 규칙에 맞지 않는 경우 |

### 기존 비밀번호 불일치 예시
```
{
  "code": "CURRENT_PASSWORD_MISMATCH",
  "message": "기존 비밀번호가 일치하지 않습니다."
}
```
### 새 비밀번호 형식 오류 예시
```
{
  "code": "VALIDATION_ERROR",
  "message": "비밀번호는 8자 이상이며 영문, 숫자, 특수문자를 각각 포함해야 합니다."
}
```
### 처리 규칙
- 입력받은 기존 비밀번호가 DB의 비밀번호 해시와 일치하는지 확인한다.
- 새 비밀번호는 최소 8자 이상이어야 한다.
- 새 비밀번호는 영문, 숫자, 특수문자를 각각 1개 이상 포함해야 한다.
- 새 비밀번호는 Argon2로 해시한 후 저장한다.
- 평문 비밀번호를 DB에 저장하지 않는다.
- 기존 비밀번호와 새 비밀번호를 응답에 포함하지 않는다.
----

## 5. 공통 오류 응답 형식
마이페이지 API의 오류는 모두 같은 형식을 사용합니다.
```
{
  "code": "ERROR_CODE",
  "message": "오류 내용입니다."
}
```

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

# 05_signout.md - API 명세서(회원탈퇴)

## 1. API 개요 (회원탈퇴)

| 항목 | 내용 |
| --- | --- |
| API 이름 | 사용자 회원탈퇴 API |
| 설명 | 본인 계정의 회원탈퇴(영구 삭제) API |
| 엔드포인트(Endpoint) | `/api/v1/auth/me` |
| 메서드(Method) | `DELETE` |
| 인증 필요 여부 | Y |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |
| Authorization | Bearer {access_token} | JWT 엑세스 토큰 인증 헤더 |
---

## 3. 응답(Response)

### 성공

- 204 No Content

    ```
    (응답 본문 없음)
    ```

### 실패

- 401 Unauthorized

    ```json
    {
      "code": "AUTHENTICATION_REQUIRED",
      "message": "인증 정보가 제공되지 않았습니다."
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | code | string | 인증 필요 안내 오류 코드 |
    | message | string | 오류 원인 설명 |

- 401 Unauthorized

    ```json
    {
      "code": "INVALID_TOKEN",
      "message": "유효하지 않거나 만료된 토큰입니다."
    }
    ```

    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | code | string | 토큰 검증 실패 오류 코드 |
    | message | string | 에러 메시지 |

---

## 4. 비고

- 회원 탈퇴가 성공하면 해당 사용자와 매핑된 모든 정보는 데이터베이스에서 즉시 하드딜리트(Hard Delete)된다.
- Cascade 규칙에 따라 사용자 탈퇴 시 사용자가 생성했던 모든 하위 연관 데이터가 같이 정리된다.
<<<<<<< HEAD
=======

---

# 비밀번호 입력 보안 명세 (NFR-USER-002)

## 1. 개요

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | `NFR-USER-002` |
| 분류 | 비기능 요구사항 (Non-Functional Requirement) |
| 기능 명 | 비밀번호 입력 보안 (Password Input Security) |
| 설명 | 모든 비밀번호 입력 시 마스킹 처리를 진행하며, 아이콘 클릭을 통해 입력한 비밀번호를 확인할 수 있도록 한다. |
| 적용 범위 | 회원가입, 로그인, 비밀번호 변경 등 모든 비밀번호 입력 필드 |

---

## 2. 요청 및 UI 규칙 (Request & UI Rules)

### 2.1 마스킹 (Masking) 처리 규칙

- 비밀번호 입력 필드의 HTML `type` 속성은 기본적으로 `password`를 사용한다.
- 입력된 문자는 화면상에 불투명한 마스킹 기호(`*` 또는 `●`)로 표시하여 외부에 노출되지 않도록 한다.
- 브라우저 자동완성 기능 구분을 위해 용도에 맞춰 속성을 지정한다:
  - 회원가입 / 새 비밀번호: `autocomplete="new-password"`
  - 로그인 / 현재 비밀번호: `autocomplete="current-password"`

### 2.2 가시성 토글 (Visibility Toggle) 규칙

- 비밀번호 입력 필드 우측 내부에 토글 전용 버튼 아이콘을 위치시킨다.
- 토글 버튼 클릭 시 Input의 `type` 속성을 `password` $\leftrightarrow$ `text`로 실시간 전환한다.
- 토글 버튼에는 반드시 `type="button"` 속성을 부여하여 클릭 시 폼(Form)이 제출되는 현상을 방지한다.
- 토글 상태 변화에 따라 웹 접근성 속성(`aria-label`, `aria-pressed`) 및 아이콘 모습을 변경한다.

---

## 3. 명세 필드 및 상태표

### 토글 상태별 명세

| 토글 상태 | Input Type | 표시 아이콘 | aria-label (접근성 라벨) | aria-pressed |
| --- | --- | --- | --- | --- |
| **기본 (마스킹)** | `password` | Eye Icon (눈 모양) | `비밀번호 표시` | `false` |
| **활성 (보기)** | `text` | Eye Off Icon (사선 눈) | `비밀번호 숨기기` | `true` |

---

## 4. 프론트엔드 예시 (Client Implementation Example)

```html
<div class="password-field">
  <label for="password">비밀번호</label>
  <div class="input-container">
    <input 
      type="password" 
      id="password" 
      name="password" 
      autocomplete="current-password" 
      placeholder="비밀번호를 입력해 주세요" 
      required
    />
    <button 
      type="button" 
      id="togglePasswordBtn" 
      class="toggle-btn" 
      aria-label="비밀번호 표시" 
      aria-pressed="false"
    >
      <span class="icon">👁️</span>
    </button>
  </div>
</div>

<script>
  const passwordInput = document.getElementById('password');
  const toggleBtn = document.getElementById('togglePasswordBtn');

  toggleBtn.addEventListener('click', () => {
    const isPassword = passwordInput.getAttribute('type') === 'password';
    
    // Type 전환 (password <-> text)
    passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
    
    // 웹 접근성 및 아이콘 상태 변경
    toggleBtn.setAttribute('aria-pressed', isPassword ? 'true' : 'false');
    toggleBtn.setAttribute('aria-label', isPassword ? '비밀번호 숨기기' : '비밀번호 표시');
    toggleBtn.querySelector('.icon').textContent = isPassword ? '🙈' : '👁️';
  });
</script>
```

---

## 5. 비고 및 보안 지침 (Security Notes)

- **평문 노출 제어**: 가시성 토글은 UI 상에서의 표시 전환 기능일 뿐이며, 콘솔 출력(`console.log`)이나 클라이언트 스토리지(LocalStorage / SessionStorage)에 평문 비밀번호를 절대 남기지 않는다.
- **네트워크 보안**: 비밀번호 가시성 상태와 무관하게, 서버로 전송되는 모든 비밀번호 데이터는 HTTPS (TLS) 통신을 통해 안전하게 암호화되어 전송된다.
- **공통 규칙 준수**: 본 비기능 요구사항은 프로젝트 내 모든 비밀번호 입력 관련 API 및 프론트엔드 화면에 일관되게 적용한다.

---

# API 성능 명세 (NFR-USER-003)

## 1. 개요

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | `NFR-USER-003` |
| 분류 | 비기능 요구사항 (Non-Functional Requirement) |
| 기능 명 | API 성능 보장 (API Performance Guarantee) |
| 설명 | 모든 유저 API는 최대 3초 이내에 로직을 처리하고 응답하도록 설계 및 구현한다. |
| 적용 범위 | User API 도메인 전반 (`/api/v1/auth/*`, `/api/v1/users/*`, `/api/v1/admin/*`) |

---

## 2. 성능 목표 및 지표 (SLA & Metrics)

### 2.1 임계 시간 규격

- **최대 허용 응답 시간 (SLA Limit)**: **3초 (3,000ms) 이내**
- **목표 평균 응답 시간 (Target Average)**: **500ms 이내**
- 모든 정상적 비즈니스 처리(가입, 로그인, 조회, 수정, 탈퇴 등)는 클라이언트 요청 수신 시점부터 응답 송신 시점까지 3초를 초과하지 않아야 한다.

---

## 3. 성능 최적화 수립 방안 (Performance Optimization Guidelines)

### 3.1 비동기 I/O (Async I/O) 적극 활용
- DB 접근, 외부 API 호출, 네트워크 I/O 작업 시 FastAPI의 `async / await` 비동기 루프 및 `AsyncSession`을 적용하여 컴퓨팅 자원의 대기(Blocking)를 최소화한다.

### 3.2 데이터베이스 조회 최적화 & 인덱싱
- 회원 검색 및 중복 체킹에 빈번히 조회되는 `email`, `phone_number` 컬럼에 DB Index를 생성하여 탐색 속도를 최적화한다.
- 목록 조회 시 페이지네이션(`page`, `size`)을 필수로 적용하여 대용량 데이터 조회에 따른 지연을 방지한다.

### 3.3 비밀번호 해싱 처리 최적화
- Argon2 해시 알고리즘 적용 시 보안성을 확보하되, CPU 튜닝 파라미터를 적절히 설정하여 해싱 처리 지연 시간이 500ms를 넘지 않도록 조정한다.

---

## 4. 성능 검증 및 테스트 방법 (Verification Plan)

| 검증 항목 | 검증 도구 | 기준 및 목표 |
| --- | --- | --- |
| **단일 API 응답 속도** | Swagger-UI / Postman | 모든 API의 처리 시간 $\le$ 3.0초 |
| **동시성 및 부하 테스트** | Locust / K6 | 동시 사용자 50명 조건에서 Max 응답 시간 $\le$ 3.0초 |
| **쿼리 튜닝 검증** | MySQL `EXPLAIN` | Index Scan 동작 확인 및 Full Table Scan 방지 |

---

## 5. 비고 및 타임아웃 오류 예시

- 처리 로직 지연으로 인해 3초 초과 발생 시 타임아웃 예외(`504 Gateway Timeout` 또는 `500 Internal Server Error`)를 반환하도록 미들웨어 차원의 가이드라인을 준수한다.

### 타임아웃 오류 응답 예시 (504 Gateway Timeout)

```json
{
  "code": "REQUEST_TIMEOUT",
  "message": "요청 처리 시간이 허용 시간(3초)을 초과하였습니다."
}
```


>>>>>>> origin/feat/1,10,11,12code
