import sys
import time
import subprocess
import threading

sys.path.insert(0, 'D:/files/Gproject/1/backend')

def run_celery_worker():
    proc = subprocess.Popen(
        ['celery', '-A', 'app.core.celery_app', 'worker', '--loglevel=info'],
        cwd='D:/files/Gproject/1/backend',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return proc

print("启动 Celery worker...")
worker_proc = run_celery_worker()

print("等待 worker 启动 (5秒)...")
time.sleep(5)

print("\n测试 Celery 任务...")

from app.tasks import add, multiply
from celery.result import AsyncResult

print("\n1. 测试 add 任务 (2 + 3)...")
task1 = add.delay(2, 3)
print(f"   任务ID: {task1.id}")
time.sleep(2)
result1 = AsyncResult(task1.id)
print(f"   状态: {result1.status}")
if result1.ready():
    print(f"   结果: {result1.result}")
else:
    print(f"   等待结果...")

print("\n2. 测试 multiply 任务 (4 * 5)...")
task2 = multiply.delay(4, 5)
print(f"   任务ID: {task2.id}")
time.sleep(2)
result2 = AsyncResult(task2.id)
print(f"   状态: {result2.status}")
if result2.ready():
    print(f"   结果: {result2.result}")
else:
    print(f"   等待结果...")

time.sleep(3)

print("\n3. 再次检查结果...")
result1 = AsyncResult(task1.id)
result2 = AsyncResult(task2.id)
print(f"   add(2,3) - 状态: {result1.status}, 结果: {result1.result if result1.ready() else 'N/A'}")
print(f"   multiply(4,5) - 状态: {result2.status}, 结果: {result2.result if result2.ready() else 'N/A'}")

print("\n停止 Celery worker...")
worker_proc.terminate()
worker_proc.wait(timeout=5)

print("\n✅ Task 1.4 Celery 集成测试完成!")
