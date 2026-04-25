from app.core.celery_app import celery_app

@celery_app.task(name='app.tasks.add')
def add(x: int, y: int) -> int:
    """示例任务：加法运算"""
    return x + y


@celery_app.task(name='app.tasks.multiply')
def multiply(x: int, y: int) -> int:
    """示例任务：乘法运算"""
    return x * y
