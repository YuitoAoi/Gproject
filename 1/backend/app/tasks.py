from celery import shared_task
from app.core.celery_app import celery_app

@shared_task
def add(x: int, y: int) -> int:
    """示例任务：加法运算"""
    return x + y

@shared_task
def multiply(x: int, y: int) -> int:
    """示例任务：乘法运算"""
    return x * y