from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Config(BaseSettings):

    BACKEND_HOST: str = '0.0.0.0'
    BACKEND_PORT: str = '8000'
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000","http://localhost:5173"]
    PROJECT_NAME: str = 'LLaMA-Factory Workstation'
    VERSION: str = '1.0.0'

    DATABASE_URL: str = 'sqlite:///gproject.db'
    REDIS_URL: str = 'redis://localhost:6379/0'

    BACKEND_CORS_ORIGINS: List[str] = ['http://localhost:3000', 'http://localhost:5173']

    CELERY_BROKER_URL: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND: str = 'redis://localhost:6379/2'

    DATASETS_DIR: str = str(Path(__file__).resolve().parents[2] / "datasets")

    GRAPHGEN_API_URL: str = "http://localhost:8001/api/v1"
    SYNTHESIZER_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    SYNTHESIZER_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SYNTHESIZER_API_KEY: str = "your-api-key"
    TRAINEE_MODE: str = "Qwen/Qwen2.5-7B-Instruct"
    TRAINEE_BASE_URL: str = "https://api.siliconflow.cn/v1"
    TRAINEE_API_KEY: str = "your-api-key"
    class Config:
        env_file = '.env'


config = Config()
