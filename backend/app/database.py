import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load backend/.env regardless of the terminal's working directory.
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE)

required_settings = [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
]

missing = [
    key for key in required_settings
    if not os.getenv(key)
]

if missing:
    raise RuntimeError(
        f"Missing database settings in {ENV_FILE}: {', '.join(missing)}"
    )

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
