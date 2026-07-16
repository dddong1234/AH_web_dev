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
