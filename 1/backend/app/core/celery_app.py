from celery import Celery

celery_app = Celery(
    'llama_factory',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/2',
    include=['app.tasks'],
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    broker_connection_retry_on_startup=True,
)
