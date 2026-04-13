from app.db.session import engine, Base
import app.db.models

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("正在创建数据库表...")
    init_db()
    print("数据库表创建完成！")