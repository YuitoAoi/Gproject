from pydantic_settings import BaseSettings


from urllib.parse import urlparse, urlunparse


class Config(BaseSettings):
    PROJECT_NAME: str = 'LLaMA-Factory Workstation'
    VERSION: str = '1.0.0'
    model_config = {"extra": "ignore", "env_file": ".env"}

    CACHE_DIR: str = "./cache"
    LOG_DIR: str = "./logs"
    DATASETS_DIR: str = "data/datasets"

    HOST: str = '0.0.0.0'
    PORT: int = 8088
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]


    DATABASE_URL: str = "mysql+pymysql://root:example@mysql:3306/llama_factory"
    REDIS_URL: str = 'redis://localhost:6379/0'

    @property
    def CELERY_BROKER_URL(self) -> str:
        parsed = urlparse(self.REDIS_URL)
        return urlunparse(parsed._replace(path="/1"))

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        parsed = urlparse(self.REDIS_URL)
        return urlunparse(parsed._replace(path="/2"))

    SUPER_USER_EMAIL: str = "super@user.net"
    SUPER_USER_PASSWORD: str = "superUser@123"
    JWT_SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 21600

    LLAMAFACTORY_URL: str = "http://localhost:8000"
    LLAMAFACTORY_API_PREFIX: str = "/v1"
    LLAMAFACTORY_TIMEOUT_MS: int = 30000
    LLAMAFACTORY_RETRIES: int = 2
    LLAMAFACTORY_DATA_DIR: str = "data/llamafactory/data"
    LLAMAFACTORY_DATASET_INFO_PATH: str = "data/llamafactory/data/dataset_info.json"
    LLAMAFACTORY_JOB_DIR: str = "data/llamafactory/jobs"
    LLAMAFACTORY_TRAIN_COMMAND: str = "llamafactory-cli"
    LLAMAFACTORY_POLL_INTERVAL_SECONDS: int = 5
    GRAPHGEN_API_URL: str = "http://localhost:8001/api/v1"
    SYNTHESIZER_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    SYNTHESIZER_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SYNTHESIZER_API_KEY: str = "your-api-key"
    TRAINEE_MODE: str = "Qwen/Qwen2.5-7B-Instruct"
    TRAINEE_BASE_URL: str = "https://api.siliconflow.cn/v1"
    TRAINEE_API_KEY: str = "your-api-key"


config = Config()
