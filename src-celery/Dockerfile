FROM python:3.12-slim

ENV TZ=Asia/Shanghai
ENV PYTHONPATH=/app

WORKDIR /app

RUN pip install --no-cache-dir poetry

# 从 src-celery/ 复制依赖文件（build context = 项目根）
COPY src-celery/pyproject.toml src-celery/poetry.lock* ./
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root \
    || pip install celery httpx redis pydantic-settings

# 复制 celery worker 自身源码
COPY src-celery/ .
# 复制 backend 源码（供 training_monitor_task 等跨容器任务使用）
COPY src-backend/src/ ./src/

CMD ["celery", "-A", "main", "worker", "--loglevel=info", "--concurrency=1"]