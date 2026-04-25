import sys
import time
sys.path.insert(0, 'D:/files/Gproject/1/backend')

from app.core.celery_app import celery_app

celery_app.conf.update(
    broker_url='redis://localhost:6379/1',
    result_backend='redis://localhost:6379/2',
)

print("直接使用 celery_app 发送任务...")

result = celery_app.send_task('app.tasks.add', args=[2, 3])
print(f"任务ID: {result.id}")
print(f"状态: {result.status}")

time.sleep(2)
print(f"等待后状态: {result.status}")
if result.ready():
    print(f"结果: {result.result}")
else:
    print("任务尚未完成")
