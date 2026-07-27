# AI Health Web Assignment

## 처음 실행하기

### 준비 사항

- Python 3.13 이상
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop 또는 로컬 MySQL 8.0

프로젝트를 처음 내려받은 팀원은 아래 순서대로 실행한다.

```bash
cp .env.example .env
uv sync
docker compose up -d mysql
uv run alembic upgrade head
uv run python scripts/seed_admin.py
uv run fastapi run app/main.py
```

앱은 `http://localhost:8000/` 또는 `http://0.0.0.0:8000/`에서 확인할 수 있다.

기본 로컬 관리자 계정은 다음과 같다.

```text
이메일: admin@example.com
비밀번호: Admin1234!
```

관리자 계정은 `.env`의 `ADMIN_EMAIL`, `ADMIN_PASSWORD`로 변경할 수 있다.
`scripts/seed_admin.py`는 여러 번 실행해도 동일 이메일의 계정을 관리자 상태로
갱신하므로 팀원이 각자 로컬 DB에서 실행해도 된다.

AI 예측에 필요한 모델 가중치
`worker/models/v8_lite_densenet121_fp16.pth`도 저장소에 포함되어 있다.

### Docker를 사용하지 않는 경우

로컬 MySQL에 `.env`와 같은 데이터베이스 및 사용자를 생성한 뒤
`uv run alembic upgrade head`부터 실행한다.

### 실행 확인

서버 실행 후 다음 주소가 정상 응답하는지 확인한다.

```text
http://localhost:8000/healthcheck
http://localhost:8000/
```

로컬 MySQL 컨테이너를 종료할 때는 다음 명령을 실행한다.

```bash
docker compose stop mysql
```

## Alembic Migration Guide

이 프로젝트는 데이터베이스 마이그레이션을 위해 Alembic을 사용합니다.

### 1. 마이그레이션 파일 생성 (자동 생성)
모델(`app/models/`)이 변경된 경우 다음 명령어를 실행하여 마이그레이션 파일을 생성합니다.
```bash
uv run alembic revision --autogenerate -m "변경 내용 설명"
```

### 2. 데이터베이스에 반영
생성된 마이그레이션을 데이터베이스에 적용하려면 다음 명령어를 실행합니다.
```bash
uv run alembic upgrade head
```

### 3. 이전 상태로 되돌리기 (Rollback)
마지막 마이그레이션을 취소하려면 다음 명령어를 실행합니다.
```bash
uv run alembic downgrade -1
```

## Redis 및 AI Worker 실행

FastAPI와 AI Worker는 Redis 작업 큐와 Pub/Sub을 통해 통신합니다.

- 로컬 Redis URL: `redis://localhost:6379/0`
- Docker Redis URL: `redis://redis:6379/0`
- FastAPI: AI 분석 작업 등록 및 결과 저장
- AI Worker: 작업 소비, 폐렴 추론 및 결과 발행

### GPU 환경에서 AI Worker 실행

기본 AI Worker 이미지는 CUDA PyTorch를 포함합니다. NVIDIA GPU를 컨테이너에서 사용하려면 NVIDIA Container Toolkit이 설치되어 있어야 합니다.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.gpu.yml \
  up -d mysql redis fastapi ai-worker
```

GPU 사용 여부는 다음 명령으로 확인할 수 있습니다.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.gpu.yml \
  exec ai-worker python -c "import torch; print(torch.cuda.is_available())"
```

`True`가 출력되면 GPU를 사용합니다. GPU가 없는 환경에서는 GPU 설정 파일을 적용하지 않고 기본 Compose 명령으로 실행하며, 이 경우 CPU로 추론합니다.

### 로컬 개발 의존성 설치

App과 AI Worker 의존성을 모두 설치합니다.

```bash
uv sync --all-extras
```

### Docker 이미지 빌드

```bash
docker compose build fastapi ai-worker
```

### 전체 서비스 실행

```bash
docker compose up -d mysql redis fastapi ai-worker
```

### 실행 상태 확인

```bash
docker compose ps
```

### Redis 연결 확인

```bash
docker compose exec redis redis-cli ping
```

정상 응답:

```text
PONG
```

### AI Worker 로그 확인

```bash
docker compose logs -f ai-worker
```

AI Worker가 Redis 작업 큐 대기 상태로 실행되면 정상입니다.

### FastAPI 로그 확인

```bash
docker compose logs -f fastapi
```

### AI Worker 다중 실행

```bash
docker compose up -d --scale ai-worker=3
```

`BRPOP`을 사용하므로 하나의 작업은 여러 Worker 중 하나만 가져가서 처리합니다.

### 서비스 종료

```bash
docker compose down
```

MySQL 데이터를 포함한 볼륨까지 삭제하려면 다음 명령을 사용합니다.

```bash
docker compose down -v
```

주의: `-v` 옵션은 기존 MySQL 데이터를 삭제하므로 필요한 경우에만 사용합니다.
