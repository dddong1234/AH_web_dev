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
