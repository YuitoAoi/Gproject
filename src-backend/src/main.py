from src.app import app as app

if __name__ == "__main__":
    import sys, pathlib

    _src = pathlib.Path(__file__).resolve().parent
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

    import uvicorn
    from src.core.config import config
    uvicorn.run("src.main:app", host=config.HOST, port=int(config.PORT), reload=True)

# poetry run python -m src.main # 配置生效, 默认监听0.0.0.0:8088
# poetry run uvicorn src.main:app --reload # 监听0.0.0.0:8000