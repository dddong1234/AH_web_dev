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