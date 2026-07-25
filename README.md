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
