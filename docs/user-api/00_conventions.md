# User API 공통 규칙

## 1. 기본 정보

- Base URL: `/api/v1`
- 요청/응답 형식: `application/json`
- 문자 인코딩: `UTF-8`
- 날짜 및 시간 형식: ISO 8601
- API 문서: `/docs`
- 인증 방식: JWT Bearer Authentication

---

## 2. URL 작성 규칙

- URL에는 명사를 사용한다.
- 복수형 리소스명을 사용한다.
- 단어 구분에는 하이픈 대신 소문자와 슬래시를 사용한다.
- URL 마지막에는 슬래시를 붙이지 않는다.

### 올바른 예시

- `POST /api/v1/auth/signup`
- `GET /api/v1/users/me`
- `GET /api/v1/admin/users`
- `PATCH /api/v1/admin/users/{user_id}/role`

### 잘못된 예시

- `GET /api/v1/getUser`
- `GET /api/v1/user_list`
- `GET /api/v1/users/`

---

## 3. HTTP Method 규칙

| Method | 용도 |
|---|---|
| `GET` | 리소스 조회 |
| `POST` | 리소스 생성 및 로그인 등 명령 처리 |
| `PATCH` | 리소스 일부 수정 |
| `PUT` | 리소스 전체 교체 |
| `DELETE` | 리소스 삭제 |

회원 정보는 일부 항목만 수정하므로 `PUT`이 아닌 `PATCH`를 사용한다.

---

## 4. 인증 규칙

Access Token은 요청 헤더에 담아서 전달한다.

`Authorization: Bearer {access_token}`

- Access Token 만료 시간: 30분
- Refresh Token 만료 시간: 7일
- Refresh Token은 `HttpOnly` 쿠키로 전달한다.
- JWT payload에는 사용자 식별자인 `user_id`만 저장한다.
- Access Token이 만료되면 Refresh Token으로 재발급한다.
- Refresh Token까지 만료되면 재로그인을 요청한다.

### 인증이 필요 없는 API

- 회원가입
- 로그인
- 토큰 재발급

### 인증이 필요한 API

- 로그아웃
- 마이페이지 조회
- 회원 정보 수정
- 비밀번호 변경
- 회원 탈퇴
- 관리자 회원 관리

---

## 5. 사용자 권한 규칙

| 권한 | Enum | 접근 범위 |
|---|---|---|
| 대기자 | `PENDING` | 마이페이지 외 서비스 접근 불가 |
| 스태프 | `STAFF` | 내부 서비스 읽기·쓰기·수정 가능 |
| 관리자 | `ADMIN` | 모든 데이터와 관리자 API 접근 가능 |

- 회원가입 시 기본 권한은 `PENDING`으로 설정한다.
- 회원 권한은 관리자만 변경할 수 있다.
- 일반 사용자가 관리자 API에 접근하면 `403 Forbidden`을 반환한다.

---

## 6. Enum 규칙

Enum 값은 영문 대문자로 통일한다.

### 부서

- `RESEARCH`
- `MEDICAL`
- `DEV`

### 성별

- `M`
- `F`

### 권한

- `PENDING`
- `STAFF`
- `ADMIN`

---

## 7. 필드 이름 규칙

요청과 응답의 필드명은 `snake_case`를 사용한다.

### 예시

- `user_id`
- `phone_number`
- `access_token`
- `current_password`
- `new_password`
- `is_active`

비밀번호는 응답에 포함하지 않는다.

다음 필드는 모든 API 응답에서 제외한다.

- `password`
- `hashed_password`
- `refresh_token`

---

## 8. 성공 응답 규칙

단일 리소스 응답은 `data` 안에 담는다.

### 예시

`GET /api/v1/users/me`

응답 상태: `200 OK`

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

리소스 생성 성공은 `201 Created`를 사용한다.

응답 본문이 필요 없는 로그아웃과 회원 탈퇴는 `204 No Content`를 사용한다.

---

## 9. 목록 응답 규칙

목록 조회에는 페이지네이션을 적용한다.

### Query Parameter

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `page` | integer | 아니요 | `1` | 페이지 번호 |
| `size` | integer | 아니요 | `20` | 페이지 크기 |
| `search` | string | 아니요 | 없음 | 이메일 또는 이름 검색 |
| `department` | string | 아니요 | 없음 | 부서 필터 |

- `page`는 1 이상이어야 한다.
- `size`는 1 이상 100 이하여야 한다.

### 응답 예시

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

---

## 10. 오류 응답 규칙

오류 응답 형식은 모든 API에서 동일하게 사용한다.

{
  "code": "INVALID_CREDENTIALS",
  "message": "이메일 또는 비밀번호가 올바르지 않습니다."
}

### HTTP 상태 코드

| 상태 코드 | 사용 상황 |
|---|---|
| `200 OK` | 조회·수정·로그인 성공 |
| `201 Created` | 회원가입 성공 |
| `204 No Content` | 로그아웃·회원 탈퇴 성공 |
| `400 Bad Request` | 잘못된 요청 또는 비즈니스 규칙 위반 |
| `401 Unauthorized` | 로그인 실패, 토큰 만료 또는 토큰 오류 |
| `403 Forbidden` | 접근 권한 부족 |
| `404 Not Found` | 사용자를 찾을 수 없음 |
| `409 Conflict` | 이메일 또는 전화번호 중복 |
| `422 Unprocessable Entity` | 요청 필드 검증 실패 |
| `500 Internal Server Error` | 서버 내부 오류 |

### 공통 오류 코드

| 오류 코드 | HTTP 상태 | 설명 |
|---|---:|---|
| `VALIDATION_ERROR` | 422 | 요청값 검증 실패 |
| `INVALID_CREDENTIALS` | 401 | 이메일 또는 비밀번호 불일치 |
| `INVALID_TOKEN` | 401 | 유효하지 않은 토큰 |
| `ACCESS_TOKEN_EXPIRED` | 401 | Access Token 만료 |
| `REFRESH_TOKEN_EXPIRED` | 401 | Refresh Token 만료 |
| `AUTHENTICATION_REQUIRED` | 401 | 인증 정보 없음 |
| `PERMISSION_DENIED` | 403 | 접근 권한 부족 |
| `USER_NOT_FOUND` | 404 | 사용자 없음 |
| `EMAIL_ALREADY_EXISTS` | 409 | 이메일 중복 |
| `PHONE_NUMBER_ALREADY_EXISTS` | 409 | 전화번호 중복 |
| `CURRENT_PASSWORD_MISMATCH` | 400 | 기존 비밀번호 불일치 |

---

## 11. 입력값 검증 규칙

### 이메일

- 올바른 이메일 형식이어야 한다.
- 중복된 이메일은 사용할 수 없다.
- 저장 및 비교 전에 소문자로 정규화한다.

### 비밀번호

- 최소 8자 이상이어야 한다.
- 영문, 숫자, 특수문자를 각각 1개 이상 포함한다.
- 평문 비밀번호를 Database에 저장하지 않는다.
- 비밀번호 해시에는 Argon2를 사용한다.

### 이름

- 2자 이상 20자 이하로 제한한다.

### 휴대폰 번호

- 숫자만 입력한다.
- 하이픈은 제거한 상태로 저장한다.
- 국내 휴대폰 번호 형식인 `010`으로 시작하는 11자리로 제한한다.
- 중복된 휴대폰 번호는 사용할 수 없다.

---

## 12. API 명세 작성 양식

각 담당자는 다음 양식으로 API 명세를 작성한다.

### API 이름

- 요구사항 ID:
- Method:
- URL:
- 설명:
- 인증 필요 여부:
- 필요 권한:

#### Path Parameter

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|

#### Query Parameter

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|

#### Request Body

{
  "field": "value"
}

#### 성공 응답

- Status Code:

{
  "data": {}
}

#### 실패 응답

| Status Code | 오류 코드 | 발생 조건 |
|---:|---|---|

#### 처리 규칙

- 처리 규칙을 작성한다.
- 권한 검증 조건을 작성한다.
- 중복 및 예외 조건을 작성한다.