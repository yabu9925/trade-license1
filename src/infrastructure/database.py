from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

SQLALCHEMY_DATABASE_URL = "sqlite:///./trade_license.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Import all models here so they are registered on Base
    from src.infrastructure.trade_license.persistence.schema import ApplicationRecord
    from src.infrastructure.auth.persistence.schema import UserRecord
    from src.infrastructure.notifications.persistence.schema import NotificationRecord
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
