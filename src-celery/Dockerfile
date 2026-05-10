FROM python:3.12-slim

ENV TZ=Asia/Shanghai

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root \
    || pip install celery httpx redis pydantic-settings

COPY . .

CMD ["celery", "-A", "main", "worker", "--loglevel=info", "--concurrency=1"]
