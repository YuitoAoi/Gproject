from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = 'LLaMA-Factory Workstation'
    VERSION: str = '1.0.0'
    API_V1_STR: str = '/api/v1'

    DATABASE_URL: str = 'mysql+pymysql://root:password@localhost:3306/llama_factory'

    REDIS_URL: str = 'redis://localhost:6379/0'

    BACKEND_CORS_ORIGINS: List[str] = ['http://localhost:3000', 'http://localhost:5173']

    CELERY_BROKER_URL: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND: str = 'redis://localhost:6379/2'

    class Config:
        env_file = '.env'


settings = Settings()
