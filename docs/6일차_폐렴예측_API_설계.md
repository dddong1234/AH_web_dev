# 6일차 폐렴 예측 API 설계

## 1. 문서 목적

- Stage 6 폐렴 예측 요구사항과 팀 공통규칙을 하나의 API 계약으로 정리한다.
- 모델 추론 코드와 API·DB 코드가 동일한 입력 및 반환 형식을 사용하도록 한다.
- 구현 전에 권한, 저장 결과 재사용, 응답 형식, 오류 및 성능 기준을 고정한다.

---

## 2. 요구사항 추적표

| 요구사항 ID | 구분 | 기능 요약 | API 반영 내용 |
| --- | --- | --- | --- |
| `REQ-PRED-001` | 기능 | AI 모델 활용 폐렴 예측 | 저장된 진료기록의 X-ray로 예측하고, 동일 `record_id + ai_model` 결과가 있으면 재추론 없이 반환한다. |
| `REQ-PRED-002` | 기능 | AI 폐렴 예측 결과 조회 | 진료기록 상세 화면에서 해당 진료기록의 AI 예측 결과 목록을 조회한다. |
| `NFR-PRED-001` | 비기능 | AI 모델 평가 기준 | Recall은 최소 `0.90`, Accuracy는 보조 지표로 `0.80~0.90`을 목표로 한다. |
| `NFR-PRED-002` | 비기능 | API 성능 | 모든 API는 3초 이내 응답을 목표로 한다. |

---

## 3. Stage 범위

### 3.1 포함 범위

- 진료기록 상세에 저장된 X-ray 이미지를 사용한 폐렴 예측
- 같은 모델의 기존 예측 결과 재사용
- 신규 추론 결과 DB 저장
- 진료기록별 AI 예측 결과 목록 조회
- 폐렴 여부, 신뢰도, 선택적 heatmap URL, 모델명 및 예측 수행 일시 반환
- 사내 의료인·개발팀·연구자 권한 확인

### 3.2 제외 범위

- API 요청에서 새로운 X-ray 파일 직접 업로드
- AI 예측 결과 수정 및 삭제
- 모델 학습 및 재학습 API
- 요구사항에 없는 별도 통계·대시보드 API

---

## 4. 권한 규칙

현재 인증 모델:

- `role`: `PENDING`, `STAFF`, `ADMIN`
- `department`: `MEDICAL`, `DEV`, `RESEARCH`

요구사항 표현을 현재 코드에 매핑하면 다음과 같다.

| 요구사항 표현 | 현재 코드 매핑 |
| --- | --- |
| 사내 의료인, 개발팀, 연구자 | `role in {STAFF, ADMIN}` |
| 승인 대기 사용자 | `role == PENDING`, 접근 불가 |

공통 규칙:

- 두 API 모두 `require_staff_or_admin()` dependency를 사용한다.
- JWT 파싱이나 권한 판별을 router에 중복 구현하지 않는다.
- 인증 누락은 `401`, 권한 부족은 `403`으로 응답한다.

---

## 5. 공통 API 규칙

### 5.1 URL 및 ID

- Base URL: `/api/v1`
- 기존 진료기록 URL 구조를 유지한다.
- `patient_id`, `record_id`는 1 이상의 정수다.
- `record_id`는 URL의 `patient_id`에 속한 진료기록이어야 한다.

### 5.2 시간 및 정렬

- DB 저장 시간은 UTC를 기준으로 한다.
- API 응답 시간은 ISO 8601 형식으로 반환한다.
- 목록은 `created_at DESC`, `id DESC` 순으로 정렬한다.

### 5.3 페이지네이션

- `offset`, `limit` 방식을 사용한다.
- 기본값은 `offset=0`, `limit=20`이다.
- `limit` 최댓값은 `100`이다.

### 5.4 Confidence

- 공용 응답의 `confidence`는 `0.00~100.00` 범위의 백분율 값으로 반환한다.
- 모델 추론 코드가 `0.0~1.0` 값을 반환하는 경우 Service 계층에서 백분율로 변환한다.
- 소수점 둘째 자리까지 저장 및 반환한다.

### 5.5 Heatmap

- 요구사항 원문의 `Hitmap`은 `Heatmap`을 의미하는 것으로 해석한다.
- API 필드명은 팀 공통규칙에 따라 `heatmap_url`을 사용한다.
- heatmap이 생성되지 않는 모델에서는 `null`을 반환한다.

### 5.6 오류 응답 포맷

프로젝트 공통 오류 형식을 사용한다.

```json
{
  "code": "MEDICAL_RECORD_NOT_FOUND",
  "message": "Medical record not found"
}
```

### 5.7 HTTP 상태 코드

- 예측 API는 신규 추론 결과를 저장한 경우와 기존 결과를 재사용한 경우 모두 `200 OK`를 반환한다.
- 사용자 관점에서는 두 경우 모두 동일한 예측 결과 조회 동작이며, 응답 형식도 동일하게 유지한다.

---

## 6. 데이터 모델 계약

### 6.1 AIAnalysisResult

| 필드 | 타입 | 제약 및 설명 |
| --- | --- | --- |
| `id` | bigint | PK |
| `record_id` | bigint | `medical_records.id` FK, required |
| `is_pneumonia` | boolean | required |
| `confidence` | numeric(5, 2) | required, `0.00~100.00` |
| `heatmap_url` | varchar(255) | nullable |
| `ai_model` | varchar(50) | required |
| `created_at` | datetime | required, UTC |
| `updated_at` | datetime | nullable, UTC |

관계 및 무결성 규칙:

- `MedicalRecord 1 : N AIAnalysisResult`
- 동일한 진료기록에 서로 다른 모델의 결과를 저장할 수 있다.
- 같은 모델의 중복 결과를 막기 위해 `UNIQUE(record_id, ai_model)` 제약을 둔다.
- `record_id`와 `ai_model`을 이용한 기존 결과 조회가 빈번하므로 복합 인덱스를 사용한다.
- 진료기록 삭제 시 연결된 AI 분석 결과도 함께 삭제되도록 `ON DELETE CASCADE`를 사용한다.

현재 모델 구현에서 보완할 항목:

- `heatmap_url`을 nullable로 변경
- `record_id + ai_model` 복합 유일 제약 추가
- `record_id` FK에 `ondelete="CASCADE"` 적용
- `MedicalRecord`와 `AIAnalysisResult` relationship 연결

---

## 7. 모델 추론 연동 계약

### 7.1 API Service 공용 인터페이스

```python
async def get_or_create_ai_analysis(
    db,
    record_id: int,
    model_name: str,
) -> dict:
    """
    1. record_id에 연결된 X-ray 이미지를 조회한다.
    2. 같은 record_id + model_name 조합의 저장 결과가 있으면 반환한다.
    3. 저장 결과가 없으면 AI 추론을 수행한다.
    4. 추론 결과를 저장한 뒤 반환한다.
    """
```

### 7.2 추론 코드 입력

- 진료기록 저장 시 생성된 `XrayImage.image_url`을 실제 로컬 파일 경로로 변환하여 사용한다.
- API에서 별도 이미지 파일을 전달받지 않는다.
- Stage 5 규칙에 따라 진료기록 저장 시 업로드한 X-ray 1개를 사용한다.
- X-ray가 존재하지 않으면 추론을 수행하지 않고 `422 XRAY_IMAGE_NOT_FOUND`를 반환한다.

### 7.3 추론 코드 반환 형식

모델 추론 모듈은 `worker/model.py`, 함수명은 `predict_pneumonia`로 고정한다.
PyTorch 추론은 동기 연산이므로 추론 함수는 동기 함수로 구현하고 API Service에서 별도 스레드로 실행한다.

```python
from pathlib import Path


def predict_pneumonia(image_path: str | Path) -> dict:
    """
    저장된 X-ray 이미지로 폐렴 여부를 예측한다.

    Returns:
        {
            "is_pneumonia": bool,
            "confidence": float,
            "heatmap_url": str | None,
        }
    """
```

모델 추론 담당 코드와 API Service 사이의 반환 계약은 다음과 같다.

```json
{
  "is_pneumonia": true,
  "confidence": 94.5,
  "heatmap_url": null
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `is_pneumonia` | bool | 폐렴 예측 여부 |
| `confidence` | float | `0.00~100.00` 백분율 |
| `heatmap_url` | string 또는 null | 생성된 heatmap URL |

API Service 호출 예시:

```python
result = await asyncio.wait_for(
    asyncio.to_thread(predict_pneumonia, image_path),
    timeout=2.5,
)
```

### 7.4 모델명 및 버전

- 클라이언트는 모델명을 요청값으로 전달하지 않는다.
- 서버가 현재 운영 모델명을 `team-model-v1`으로 고정하여 Service에 전달한다.
- 모델 파일, 입력 전처리, 출력 해석 또는 threshold가 변경되면 모델 버전을 증가시킨다.

```python
AI_MODEL_NAME = "team-model-v1"
```

---

## 8. 공용 응답 형식

### 8.1 단일 결과

```json
{
  "id": 1,
  "record_id": 10,
  "is_pneumonia": true,
  "confidence": 94.5,
  "heatmap_url": "/media/heatmaps/record-10.png",
  "ai_model": "team-model-v1",
  "created_at": "2026-07-22T10:00:00Z",
  "updated_at": null
}
```

### 8.2 필드 설명

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | int | AI 분석 결과 ID |
| `record_id` | int | 대상 진료기록 ID |
| `is_pneumonia` | bool | 폐렴 여부 |
| `confidence` | float | 예측 신뢰도 백분율 |
| `heatmap_url` | string 또는 null | heatmap 이미지 URL |
| `ai_model` | string | 사용한 모델명 |
| `created_at` | datetime | 예측 수행 일시 |
| `updated_at` | datetime 또는 null | 수정 시각 |

응답 필드명은 팀 합의 없이 변경하지 않는다.

---

## 9. API 목록

| Method | Path | 설명 | 요구사항 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/patients/{patient_id}/medical-records/{record_id}/ai-analyses` | 기존 결과 반환 또는 신규 폐렴 예측 수행 | `REQ-PRED-001` |
| `GET` | `/api/v1/patients/{patient_id}/medical-records/{record_id}/ai-analyses` | 해당 진료기록의 예측 결과 목록 조회 | `REQ-PRED-002` |

---

## 10. API 상세 명세

### 10.1 폐렴 예측 실행 또는 기존 결과 반환

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| Path | `/api/v1/patients/{patient_id}/medical-records/{record_id}/ai-analyses` |
| 권한 | `STAFF`, `ADMIN` |
| Content-Type | 별도 Request Body 없음 |

Path Parameters:

| 필드 | 타입 | 제약 | 설명 |
| --- | --- | --- | --- |
| `patient_id` | integer | `ge=1` | 환자 ID |
| `record_id` | integer | `ge=1` | 진료기록 ID |

처리 순서:

1. 인증 및 `STAFF`, `ADMIN` 권한을 확인한다.
2. `patient_id`에 속한 `record_id`인지 확인한다.
3. 진료기록에 저장된 X-ray 이미지가 존재하는지 확인한다.
4. `record_id + ai_model`로 저장된 결과를 조회한다.
5. 기존 결과가 있으면 모델을 호출하지 않고 `200 OK`로 반환한다.
6. 기존 결과가 없으면 저장된 X-ray로 AI 추론을 수행한다.
7. 결과를 DB에 저장하고 `200 OK`로 반환한다.

성공:

- 신규 추론 및 저장: `200 OK`
- 기존 결과 재사용: `200 OK`

응답 본문:

```json
{
  "id": 1,
  "record_id": 10,
  "is_pneumonia": true,
  "confidence": 94.5,
  "heatmap_url": null,
  "ai_model": "team-model-v1",
  "created_at": "2026-07-22T10:00:00Z",
  "updated_at": null
}
```

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `404 PATIENT_NOT_FOUND`
- `404 MEDICAL_RECORD_NOT_FOUND`
- `422 XRAY_IMAGE_NOT_FOUND`
- `500 AI_INFERENCE_FAILED`
- `504 REQUEST_TIMEOUT`

### 10.2 폐렴 예측 결과 목록 조회

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| Path | `/api/v1/patients/{patient_id}/medical-records/{record_id}/ai-analyses` |
| 권한 | `STAFF`, `ADMIN` |

Query Parameters:

| 필드 | 타입 | 기본값 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `offset` | integer | `0` | `ge=0` | 조회 시작 위치 |
| `limit` | integer | `20` | `1~100` | 조회 건수 |

성공:

- `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "record_id": 10,
      "is_pneumonia": true,
      "confidence": 94.5,
      "heatmap_url": null,
      "ai_model": "team-model-v1",
      "created_at": "2026-07-22T10:00:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 20
}
```

오류:

- `401 AUTHENTICATION_REQUIRED`
- `403 PERMISSION_DENIED`
- `404 PATIENT_NOT_FOUND`
- `404 MEDICAL_RECORD_NOT_FOUND`
- `422 VALIDATION_ERROR`
- `500 INTERNAL_SERVER_ERROR`

---

## 11. 오류 코드

| 상황 | 상태 코드 | 오류 코드 |
| --- | --- | --- |
| 인증 누락 또는 만료 | `401` | `AUTHENTICATION_REQUIRED` |
| 권한 부족 | `403` | `PERMISSION_DENIED` |
| 환자 없음 | `404` | `PATIENT_NOT_FOUND` |
| 진료기록 없음 | `404` | `MEDICAL_RECORD_NOT_FOUND` |
| 진료기록에 X-ray 없음 | `422` | `XRAY_IMAGE_NOT_FOUND` |
| 요청값 검증 실패 | `422` | `VALIDATION_ERROR` |
| 동일 결과 저장 충돌 | `409` | `AI_ANALYSIS_ALREADY_EXISTS` |
| 모델 추론 실패 | `500` | `AI_INFERENCE_FAILED` |
| 서버 내부 오류 | `500` | `INTERNAL_SERVER_ERROR` |
| 3초 초과 | `504` | `REQUEST_TIMEOUT` |

동시 요청으로 `record_id + ai_model` 저장 충돌이 발생한 경우 rollback 후 이미 저장된 결과를 다시 조회하여 반환하는 것을 우선한다. 정상적인 재사용 흐름에서는 `409`를 사용자에게 노출하지 않는다.

---

## 12. 저장 결과 재사용 규칙

1. 모델명은 코드에서 관리하는 고정 버전 문자열을 사용한다.
2. 추론 전에 반드시 `record_id + ai_model`로 기존 결과를 조회한다.
3. 기존 결과가 있으면 X-ray 파일을 다시 읽거나 모델을 호출하지 않는다.
4. 기존 결과가 없을 때만 추론을 수행하고 결과를 저장한다.
5. DB 복합 유일 제약으로 동시 요청에 의한 중복 저장을 방지한다.
6. 모델 파일이나 전처리·threshold가 변경되면 `ai_model` 버전을 변경한다.

---

## 13. 비기능 요구사항

### 13.1 모델 평가 기준

- TP: 폐렴 환자를 폐렴으로 예측
- FP: 정상 환자를 폐렴으로 예측
- FN: 폐렴 환자를 정상으로 예측하며 가장 위험한 오류로 관리
- TN: 정상 환자를 정상으로 예측
- Recall: `TP / (TP + FN)`, 최소 `0.90`, 목표 `0.90~0.95`
- Accuracy: `(TP + TN) / 전체 표본 수`, 보조 지표로 `0.80~0.90` 목표

모델 평가 수치와 검증 데이터셋 결과는 모델 담당자가 별도 검증 자료로 관리한다. API는 확정된 모델의 예측 결과를 저장하고 반환한다.

### 13.2 API 성능

- 모든 API는 3초 이내 응답을 목표로 한다.
- 측정 범위는 API 서버가 요청을 받은 시점부터 응답 생성을 완료한 시점까지다.
- 인증·권한 확인, DB 조회, X-ray 읽기, 전처리, 추론, 결과 저장 및 응답 생성을 측정 범위에 포함한다.
- 사용자 네트워크 전송 시간, 프론트엔드 렌더링 시간, 서버 시작 및 모델 최초 로딩 시간은 제외한다.
- 모델은 요청마다 다시 로드하지 않고 애플리케이션 생명주기 동안 재사용한다.
- 기존 결과가 있으면 DB 조회만 수행하고 모델 추론을 생략한다.
- `record_id + ai_model` 조회에 적절한 인덱스를 사용한다.
- 목록 조회는 페이지네이션을 적용한다.
- 정상·폐렴 샘플 모두에 대해 응답 시간을 측정한다.
- 모델 추론은 `asyncio.to_thread()`로 실행하고 `asyncio.wait_for(..., timeout=2.5)`를 적용한다.
- 추론이 2.5초를 초과하면 `504 REQUEST_TIMEOUT`을 반환한다.
- 남은 약 0.5초는 인증, DB 처리 및 응답 생성에 사용한다.

---

## 14. 테스트 계획

공용 테스트 이미지:

- 위치: `sample_data/xray/`
- 정상 X-ray 1개
- 폐렴 X-ray 1개

모델 추론 담당자와 API 담당자는 반드시 같은 두 파일로 추론 결과와 API 응답을 비교한다.

| 테스트 | 기대 결과 |
| --- | --- |
| 정상 X-ray 신규 예측 | `is_pneumonia=false`, 결과 저장 및 반환 |
| 폐렴 X-ray 신규 예측 | `is_pneumonia=true`, 결과 저장 및 반환 |
| 동일 `record_id + ai_model` 재요청 | 추론 함수를 호출하지 않고 저장 결과 반환 |
| 같은 진료기록에 다른 모델 사용 | 새로운 결과 생성 가능 |
| 결과 목록 조회 | 최신순, 페이지네이션 적용 |
| 존재하지 않는 환자 | `404 PATIENT_NOT_FOUND` |
| 존재하지 않는 진료기록 | `404 MEDICAL_RECORD_NOT_FOUND` |
| 다른 환자의 진료기록 ID 조합 | `404 MEDICAL_RECORD_NOT_FOUND` |
| X-ray가 없는 진료기록 | `422 XRAY_IMAGE_NOT_FOUND` |
| `PENDING` 사용자 접근 | `403 PERMISSION_DENIED` |
| 인증 없이 접근 | `401 AUTHENTICATION_REQUIRED` |
| 추론 실패 | `500 AI_INFERENCE_FAILED` |
| API 처리 시간 | 3초 이내 |

---

## 15. 구현 계층 책임

| 계층 | 책임 |
| --- | --- |
| Router | Path·Query 검증, 권한 dependency, Service 호출, 응답 모델 선언 |
| Schema | 단일 결과 및 페이지네이션 응답 계약 정의 |
| Service | 진료기록·X-ray 확인, 기존 결과 재사용, 추론 호출, 저장 orchestration |
| Repository | 기존 결과 조회, 목록·전체 개수 조회, 신규 결과 저장 |
| Model | DB 컬럼, FK, 복합 유일 제약 및 relationship 정의 |
| Worker/Inference | 이미지 전처리 및 폐렴 추론 수행 |

---

## 16. Merge 전 확인 항목

- [ ] 저장된 진료기록의 X-ray 이미지로 예측이 동작한다.
- [ ] 정상·폐렴 공용 샘플의 추론 결과와 API 응답이 일치한다.
- [ ] 같은 `record_id + ai_model` 결과는 재추론하지 않는다.
- [ ] 동시 요청에서도 중복 결과가 저장되지 않는다.
- [ ] 공용 응답 필드명과 타입이 명세와 일치한다.
- [ ] heatmap이 없을 때 `heatmap_url=null`을 반환한다.
- [ ] 결과 목록이 최신순으로 조회된다.
- [ ] 권한 및 오류 응답이 프로젝트 공통 규칙과 일치한다.
- [ ] API가 3초 이내에 응답한다.
- [ ] 추론 담당자와 API 담당자가 동일 테스트 이미지로 함께 검증한다.

---

## 17. 최종 확정 사항

- 모델 추론 모듈: `worker/model.py`
- 모델 추론 함수: `predict_pneumonia(image_path: str | Path) -> dict`
- 추론 실행: `asyncio.to_thread()`
- 추론 timeout: 2.5초
- API 전체 응답 목표: 요청 수신부터 응답 생성까지 3초 이내
- timeout 응답: `504 REQUEST_TIMEOUT`
