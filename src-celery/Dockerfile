FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root \
    || pip install celery httpx redis pydantic-settings

COPY . .

CMD ["celery", "-A", "main", "worker", "--loglevel=info", "--concurrency=1"]
