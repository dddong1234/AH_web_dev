# Stage 3 팀 작업 분담 및 공통 계약

## 목적
- Stage 3 구현 전에 app/worker가 같은 Redis 메시지 규약을 사용하도록 맞춘다.
- 팀장 1명, 팀원 3명이 충돌 없이 병렬 작업할 수 있게 경계를 고정한다.

## 공통 코드 위치
- [shared/ai_queue_protocol.py](/mnt/c/dev/AH_web_dev/shared/ai_queue_protocol.py)

이 파일은 FastAPI 앱과 AI Worker가 함께 사용하는 최소 계약이다.

포함 내용:
- Redis queue key
- Redis pub/sub channel naming rule
- `job_id` 생성 함수
- 작업 메시지 스키마
- 결과 메시지 스키마
- JSON 직렬화/역직렬화 함수

## Redis 계약

### Queue
- 작업 적재 key: `ai-analysis:queue`
- FastAPI는 작업 요청을 이 큐에 넣는다.
- Worker는 이 큐에서 작업을 가져간다.

### Result channel
- 결과 채널 prefix: `ai-analysis:result`
- 실제 채널명: `ai-analysis:result:{job_id}`
- FastAPI는 enqueue 후 해당 채널을 subscribe 한다.
- Worker는 처리 상태와 최종 결과를 이 채널에 publish 한다.

## 메시지 스키마

### Task message
```json
{
  "job_id": "uuid",
  "record_id": 123,
  "model_name": "v8-lite-densenet121-fp16",
  "image_path": "xray_images/2026/07/example.png"
}
```

### Result message
```json
{
  "job_id": "uuid",
  "record_id": 123,
  "model_name": "v8-lite-densenet121-fp16",
  "status": "succeeded",
  "is_pneumonia": true,
  "confidence": 0.97,
  "heatmap_path": "heatmaps/123/example.png",
  "error": null
}
```

`status`는 아래 값만 허용한다.
- `queued`
- `running`
- `succeeded`
- `failed`

## 역할 분담

### 팀장
- 공통 계약 변경 승인
- PR 병합 순서 관리
- end-to-end 테스트와 운영 규칙 정리

### 팀원 A: FastAPI app
- `app/core/redis_client.py` 작성
- `app/services/ai_analysis_service.py`에서 직접 추론 제거
- 기존 결과 조회 후 없으면 task enqueue
- 결과 채널 subscribe 후 성공 시 DB 저장, 실패 시 예외 변환

### 팀원 B: Worker
- `worker/redis_client.py` 작성
- `worker/main.py`에서 queue consume
- `running` 상태 publish
- 추론 후 `succeeded` 또는 `failed` publish

### 팀원 C: Docker and dependency
- `pyproject.toml` 의존성 그룹 정리
- `worker/Dockerfile` 작성
- `docker-compose.yml`에 `redis`, `ai-worker` 추가
- 컨테이너 조합 검증

## 구현 규칙
- `model_name`은 우선 `v8-lite-densenet121-fp16` 하나만 사용한다.
- 동일 `record_id + model_name` 결과가 이미 DB에 있으면 FastAPI는 새 작업을 만들지 않는다.
- Worker는 DB 저장을 하지 않고 추론 결과 publish까지만 담당한다.
- 최종 DB 저장 책임은 FastAPI에 둔다.
- 예외 메시지는 우선 `error` 문자열로 전달하고, 세부 예외 타입 매핑은 app 쪽에서 처리한다.


## 최소 import 예시

### FastAPI 쪽
```python
from shared.ai_queue_protocol import (
    AI_ANALYSIS_QUEUE_KEY,
    AIAnalysisResultMessage,
    build_result_channel,
    make_task_message,
)
```

### Worker 쪽
```python
from shared.ai_queue_protocol import (
    AIAnalysisTaskMessage,
    build_result_channel,
    make_failed_result,
    make_running_result,
    make_success_result,
)
```
