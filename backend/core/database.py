from core.config import get_config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


config = get_config()
Base = declarative_base()


def get_db():
    # Create SQLalchemy engine
    engine = create_engine(config["database_url"], echo=True)
    Base.metadata.create_all(engine)

    # SQLAlchemy session configuration
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
