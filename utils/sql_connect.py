from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# 获取数据库连接
def get_session():

    # 数据库引擎和会话创建
    engine = create_engine(f'sqlite:///database/raid.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    return session
