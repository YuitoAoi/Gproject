import sys
sys.path.insert(0, 'D:/files/Gproject/1/backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'mysql+pymysql://root:123456@localhost:3306/'

print("连接 MySQL...")
engine = create_engine(DATABASE_URL)

print("\n测试连接...")
with engine.connect() as conn:
    result = conn.execute(text('SHOW DATABASES'))
    print("MySQL 连接成功!")
    print("\n现有数据库:")
    for row in result:
        print(f"  - {row[0]}")

print("\n创建数据库 llama_factory...")
with engine.connect() as conn:
    conn.execute(text("CREATE DATABASE IF NOT EXISTS llama_factory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.commit()
    print("数据库创建成功!")

print("\n连接到 llama_factory 并创建表...")
from app.db.session import engine as app_engine
from app.db.init_db import init_db
init_db()

print("\n验证表是否创建...")
with app_engine.connect() as conn:
    result = conn.execute(text('SHOW TABLES'))
    print("llama_factory 中的表:")
    for row in result:
        print(f"  - {row[0]}")

print("\n✅ Task 1.3 数据库集成 完成!")
