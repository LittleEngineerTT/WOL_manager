from threading import local

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

thread_local = local()


def get_db():
    if not hasattr(thread_local, "db"):
        # Create SQLalchemy engine
        DATABASE_URL = "sqlite:///core/devices.db"
        engine = create_engine(DATABASE_URL, echo=True)

        # SQLAlchemy session configuration
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        thread_local.db = SessionLocal()
    return thread_local.db
