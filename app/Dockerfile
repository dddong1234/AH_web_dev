FROM python:3.13-slim

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY worker ./worker
COPY static ./static
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini ./

RUN uv sync --frozen --no-dev --no-install-project

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
