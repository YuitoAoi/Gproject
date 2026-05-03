from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Config(BaseSettings):

    BACKEND_HOST: str = '0.0.0.0'
    BACKEND_PORT: str = '8000'
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000","http://localhost:5173"]
    PROJECT_NAME: str = 'LLaMA-Factory Workstation'
    VERSION: str = '1.0.0'

    DATABASE_URL: str = 'mysql+pymysql://user:password@localhost:3306/llama_factory'
    REDIS_URL: str = 'redis://localhost:6379/0'

    BACKEND_CORS_ORIGINS: List[str] = ['http://localhost:3000', 'http://localhost:5173']

    CELERY_BROKER_URL: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND: str = 'redis://localhost:6379/2'

    DATASETS_DIR: str = str(Path(__file__).resolve().parents[2] / "datasets")

    class Config:
        env_file = '.env'


config = Config()
