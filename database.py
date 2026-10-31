import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load .env file automatically when running locally
load_dotenv()

# 1. Fetch DATABASE_URL from environment variable (e.g. Supabase / PostgreSQL)
# If not provided, fallback to local SQLite (yummy.db)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./yummy.db")

# Supabase or cloud providers sometimes provide 'postgres://' or 'postgresql://'
# Ensure SQLAlchemy uses psycopg2 driver
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# SQLite requires check_same_thread=False; PostgreSQL does not
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# 2. Create engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# 3. Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class
Base = declarative_base()

# 5. Dependency to get DB session per-request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
