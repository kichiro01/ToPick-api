from sqlalchemy import create_engine
from api.models.user import Base as Base4User
from api.models.mylist import Base as Base4Mylist
from api.models.auth import Base as Base4Auth

DB_URL = "mysql+pymysql://root@db:3306/topickdb?charset=utf8mb4"
engine = create_engine(DB_URL, echo=True)

def reset_database():
    Base4User.metadata.drop_all(bind=engine)
    Base4Mylist.metadata.drop_all(bind=engine)
    Base4Auth.metadata.drop_all(bind=engine)
    Base4User.metadata.create_all(bind=engine)
    Base4Mylist.metadata.create_all(bind=engine)
    Base4Auth.metadata.create_all(bind=engine)

if __name__ == "__main__":
    reset_database()