from app.db.session import engine, Base
from app.db.models import User, Dataset, TrainingTask, TrainedModel


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    print('数据库表创建完成')


if __name__ == '__main__':
    init_db()
