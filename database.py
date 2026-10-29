from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. SQLite database URL (stored in a local file called yummy.db)
SQLALCHEMY_DATABASE_URL = "sqlite:///./yummy.db"

# 2. Create the engine (connect_args is only needed for SQLite)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class that our database models will inherit from
Base = declarative_base()

# 5. Dependency to get DB session per-request and close it cleanly
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()