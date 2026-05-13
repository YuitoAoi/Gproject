# ruff: noqa: E402
"""快速调试 upload/initiate 500 错误"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "services"))

# 模拟 lifespan 启动
from src.adapters.repositories.mysql_dataset_repo import DatasetRepositoryAdapter
from src.adapters.repositories.user_repo import UserRepositoryAdapter
from src.adapters.repositories.windows_file_repo import WindowsFileRepository
from src.core.config import config
from src.db_connections.mysql import MysqlConnection
from src.services import ServiceFactory

db_conn = MysqlConnection(database_url=config.DATABASE_URL)
try:
    db_conn.start()
    print("DB: started")
except Exception as e:
    print(f"DB: {e}")

factory = ServiceFactory(
    user_repo=UserRepositoryAdapter(db_conn),
    dataset_repo=DatasetRepositoryAdapter(db_conn),
    file_repo=WindowsFileRepository(),
)
print("Factory: created")

# 测试 chunked_upload
from src.services.chunked_upload_service import InitiateUploadRequest

try:
    svc = factory.chunked_upload()
    print("ChunkedUploadService: instantiated")
    result = svc.initiate(InitiateUploadRequest(filename="test.json", file_size=1000, file_hash="a" * 64))
    print(f"Initiate: upload_id={result.upload_id}")
except Exception:
    traceback.print_exc()

db_conn.dispose()
