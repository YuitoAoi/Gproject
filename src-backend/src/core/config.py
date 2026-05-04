from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Config(BaseSettings):
    model_config = {"extra": "ignore", "env_file": ".env"}

    # General
    CACHE_DIR: str = "./cache"
    LOG_DIR: str = "./logs"

    # Backend
    BACKEND_HOST: str = '0.0.0.0'
    BACKEND_PORT: str = '8000'
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    PROJECT_NAME: str = 'LLaMA-Factory Workstation'
    VERSION: str = '1.0.0'

    DATABASE_URL: str = "sqlite:///data/gproject.db"
    REDIS_URL: str = 'redis://localhost:6379/0'

    CELERY_BROKER_URL: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND: str = 'redis://localhost:6379/2'

    DATASETS_DIR: str = str(Path(__file__).resolve().parents[2] / "datafile" / "datasets")

    SUPER_USER_EMAIL: str = "super@user.net"
    SUPER_USER_PASSWORD: str = "superUser@123"
    JWT_SECRET_KEY: str = "your-secret-key"

    # GraphGen
    GRAPHGEN_API_URL: str = "http://localhost:8001/api/v1"
    SYNTHESIZER_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    SYNTHESIZER_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SYNTHESIZER_API_KEY: str = "your-api-key"
    TRAINEE_MODE: str = "Qwen/Qwen2.5-7B-Instruct"
    TRAINEE_BASE_URL: str = "https://api.siliconflow.cn/v1"
    TRAINEE_API_KEY: str = "your-api-key"


config = Config()
