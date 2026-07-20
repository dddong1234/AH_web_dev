# NFR-USER-003.md - API 성능 명세서

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
