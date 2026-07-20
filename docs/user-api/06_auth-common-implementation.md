# 인증 공통 구현 기준

> 이 문서는 Stage 4 User API 구현 시 팀 전체가 공통으로 따라야 하는 인증 구조를 정의한다.
>
> 대상 범위:
> - `POST /api/v1/auth/login`
> - `POST /api/v1/auth/refresh`
> - `POST /api/v1/auth/logout`
> - JWT 발급 및 검증 공통 코드
> - 인증 Dependency
> - 인증 예외 처리

---

## 1. 결정 사항

- Refresh Token은 DB 저장 기반으로 관리한다.
- 로그아웃 시 쿠키 삭제와 서버 측 폐기를 함께 수행한다.
- 인증/인가 오류 응답은 FastAPI 기본 형식 대신 전역 exception handler로 통일한다.
- JWT payload의 식별 정보는 `user_id`만 사용한다.
- Access Token 만료 시간은 30분이다.
- Refresh Token 만료 시간은 7일이다.
- Refresh Token은 `HttpOnly` 쿠키로 전달한다.

---

## 2. 구현 목표

이 공통 구조의 목적은 다음과 같다.

- 다른 팀원이 동일한 인증 dependency를 그대로 재사용할 수 있어야 한다.
- 인증 실패 응답 형식이 모든 API에서 동일해야 한다.
- Access Token과 Refresh Token의 역할이 코드 구조상 분리되어야 한다.
- Refresh Token 폐기 여부를 서버에서 검증할 수 있어야 한다.
- 에이전트가 파일 역할을 빠르게 파악할 수 있어야 한다.

---

## 3. 디렉터리 구조

아래 구조를 인증 공통 기준으로 사용한다.

```text
app/
├── apis/
│   ├── __init__.py
│   └── auth.py
├── core/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   └── handlers.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── cookies.py
│   │   ├── jwt.py
│   │   └── password.py
│   ├── config.py
│   └── db/
│       └── ...
├── models/
│   ├── __init__.py
│   ├── refresh_tokens.py
│   └── users.py
├── repositories/
│   ├── __init__.py
│   └── auth_repository.py
├── schemas/
│   ├── __init__.py
│   ├── auth.py
│   └── common.py
└── services/
    ├── __init__.py
    └── auth_service.py
```

---

## 4. 파일별 책임

### 4.1 `app/apis/auth.py`

- `/api/v1/auth/login`
- `/api/v1/auth/refresh`
- `/api/v1/auth/logout`
- `AsyncSession` dependency 주입
- 인증 dependency 주입
- Service 호출
- 쿠키 설정/삭제 반영

Router 내부에 비즈니스 로직을 넣지 않는다.

### 4.2 `app/services/auth_service.py`

- 이메일 정규화
- 비밀번호 검증
- 사용자 활성화 상태 확인
- Access Token 발급
- Refresh Token 발급
- Refresh Token 저장 및 폐기 처리
- 토큰 기반 사용자 조회

Service는 인증 관련 업무 규칙을 담당한다.

### 4.3 `app/repositories/auth_repository.py`

- 이메일 기준 사용자 조회
- ID 기준 사용자 조회
- Refresh Token 저장
- Refresh Token 해시 조회
- Refresh Token 폐기

Repository는 `AsyncSession`과 `select()` 기반으로만 구현한다.

### 4.4 `app/core/security/jwt.py`

- Access Token 생성
- Refresh Token 생성
- JWT decode 및 payload 검증
- `type` 검사
- `exp` 만료 처리

### 4.5 `app/core/security/password.py`

- Argon2 해시 생성
- Argon2 검증

### 4.6 `app/core/security/cookies.py`

- Refresh Token 쿠키 설정 함수
- Refresh Token 쿠키 삭제 함수

쿠키 설정 로직을 Router마다 중복하지 않는다.

### 4.7 `app/core/auth/dependencies.py`

- `get_current_user`
- `get_current_active_user`
- 필요 시 `get_current_admin_user`

다른 팀원은 보호가 필요한 API에서 이 dependency를 공통으로 사용한다.

### 4.8 `app/core/auth/exceptions.py`

- 인증 도메인 전용 예외 정의
- 예외에 `status_code`, `code`, `message` 포함

### 4.9 `app/core/auth/handlers.py`

- 도메인 예외를 `{code, message}` 구조로 변환
- `RequestValidationError`도 `VALIDATION_ERROR` 형식으로 통일

### 4.10 `app/schemas/common.py`

- 공통 성공 응답 래퍼
- 공통 오류 응답 구조

### 4.11 `app/schemas/auth.py`

- 로그인 요청 스키마
- 토큰 응답 스키마

### 4.12 `app/models/refresh_tokens.py`

- Refresh Token 저장용 모델
- 서버 측 폐기 여부 확인 기준 테이블

---

## 5. Refresh Token 저장 전략

문서 요구사항에는 다음 규칙이 포함된다.

- 재발급 시 폐기된 토큰인지 확인해야 한다.
- 로그아웃 시 서버에서 해당 토큰을 폐기해야 한다.

따라서 Refresh Token은 단순 JWT 검증만으로 처리하지 않고 DB 저장 기반으로 관리한다.

### 5.1 권장 테이블

테이블명 예시: `refresh_tokens`

권장 컬럼:

- `id`
- `user_id`
- `token_hash`
- `expires_at`
- `revoked_at`
- `created_at`

### 5.2 저장 원칙

- 원문 Refresh Token 전체를 DB에 저장하지 않는다.
- DB에는 토큰의 해시값만 저장한다.
- 재발급 시 쿠키의 원문 토큰을 해시한 뒤 DB와 비교한다.
- 로그아웃 시 해당 토큰 해시의 `revoked_at`을 기록한다.

### 5.3 사용자와의 관계

- 한 사용자에게 여러 Refresh Token을 허용할지 여부는 별도 정책으로 확장 가능하다.
- 현재 기본 구현은 여러 기기 로그인을 막지 않는 방향으로 두어도 된다.
- 단, 재발급과 로그아웃은 반드시 현재 쿠키 토큰 단위로 처리한다.

---

## 6. JWT payload 기준

개인정보와 권한 정보는 JWT에 넣지 않는다.

### 6.1 Access Token payload

```json
{
  "user_id": 1,
  "type": "access",
  "iat": 1784188800,
  "exp": 1784190600
}
```

### 6.2 Refresh Token payload

```json
{
  "user_id": 1,
  "type": "refresh",
  "iat": 1784188800,
  "exp": 1784793600
}
```

### 6.3 규칙

- `user_id`만 식별 정보로 사용한다.
- `type`은 `access` 또는 `refresh`만 허용한다.
- 일반 API 인증에는 Access Token만 허용한다.
- `/api/v1/auth/refresh`에는 Refresh Token만 허용한다.

---

## 7. 쿠키 규칙

쿠키명은 `refresh_token`을 사용한다.

기본 속성:

- `HttpOnly=True`
- `Path=/api/v1/auth`
- `SameSite=Lax`
- `Max-Age=604800`

운영 환경에서는 `Secure=True`를 적용한다.

로그아웃 시에는 동일한 Path로 쿠키를 삭제해야 한다.

---

## 8. 설정값 기준

`app/core/config.py`에 아래 설정을 추가한다.

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `COOKIE_SECURE`

기본값 예시:

- `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `REFRESH_TOKEN_EXPIRE_DAYS=7`
- `JWT_ALGORITHM=HS256`

`JWT_SECRET_KEY`는 반드시 환경변수로 주입한다.

---

## 9. 전역 예외 처리 기준

모든 인증/인가 관련 오류 응답은 아래 형식을 따른다.

```json
{
  "code": "INVALID_CREDENTIALS",
  "message": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

### 9.1 전역 handler 대상

- 인증 도메인 예외
- 권한 부족 예외
- `RequestValidationError`

### 9.2 기본 오류 코드 예시

- `VALIDATION_ERROR`
- `AUTHENTICATION_REQUIRED`
- `INVALID_CREDENTIALS`
- `INVALID_ACCESS_TOKEN`
- `ACCESS_TOKEN_EXPIRED`
- `REFRESH_TOKEN_REQUIRED`
- `INVALID_REFRESH_TOKEN`
- `REFRESH_TOKEN_EXPIRED`
- `REFRESH_TOKEN_REVOKED`
- `INACTIVE_USER`
- `USER_NOT_FOUND`
- `PERMISSION_DENIED`

---

## 10. API별 처리 흐름

### 10.1 로그인

1. 요청 스키마 검증
2. 이메일 trim 및 lowercase 정규화
3. DB에서 사용자 조회
4. Argon2 비밀번호 검증
5. 활성 사용자 여부 확인
6. Access Token 생성
7. Refresh Token 생성
8. Refresh Token 해시 DB 저장
9. 쿠키 설정
10. `data` 구조로 응답 반환

### 10.2 토큰 재발급

1. 쿠키에서 `refresh_token` 확인
2. JWT 서명 및 만료 검증
3. `type=refresh` 확인
4. 토큰 해시 DB 조회
5. 폐기 여부 확인
6. 사용자 조회
7. 활성 사용자 여부 확인
8. Access Token 재발급
9. `data` 구조로 응답 반환

### 10.3 로그아웃

1. Authorization 헤더에서 Access Token 추출
2. JWT 서명 및 만료 검증
3. 사용자 조회
4. 쿠키에 Refresh Token이 있으면 DB에서 폐기 처리
5. 쿠키 삭제
6. `204 No Content` 반환

---

## 11. 다른 팀원이 재사용할 공통 진입점

다른 팀원은 아래 항목을 우선 재사용한다.

- `app.core.auth.dependencies.get_current_user`
- `app.core.auth.dependencies.get_current_active_user`
- `app.core.auth.exceptions`
- `app.schemas.common`

### 예시

- 마이페이지 조회 API는 `get_current_active_user`를 사용한다.
- 관리자 회원 관리 API는 `get_current_active_user` 이후 role 검증을 추가한다.
- 인증 실패 응답은 직접 `HTTPException`을 만들지 않고 도메인 예외를 raise 한다.

---

## 12. 구현 시 주의사항

- Router, Service, Repository는 모두 `async def`로 구현한다.
- DB 접근은 `AsyncSession`과 `select()`를 사용한다.
- 비밀번호 원문과 JWT 원문을 로그에 남기지 않는다.
- Refresh Token을 Query Parameter 또는 Request Body로 받지 않는다.
- Access Token과 Refresh Token 검증 로직을 한 함수에 섞지 않는다.
- FastAPI 기본 `detail` 응답과 팀 공통 오류 응답이 혼재되지 않도록 handler를 먼저 등록한다.

---

## 13. 구현 순서 권장안

1. 설정값 추가
2. 공통 예외 및 전역 handler 구현
3. JWT/Password/Cookie 유틸 구현
4. Refresh Token 모델 및 마이그레이션 추가
5. Auth Repository 구현
6. Auth Service 구현
7. Auth Router 구현
8. `app/main.py`에 router와 handler 등록

이 순서를 지키면 다른 팀원이 중간부터 공통 dependency를 바로 재사용할 수 있다.
