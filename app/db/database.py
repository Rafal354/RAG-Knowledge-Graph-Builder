from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.config import settings

engine = create_engine(
    settings.postgres_url,
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)   