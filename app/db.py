import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Fetch the database URL from the environment variables set in docker-compose.yml
# fallback string just in case it runs outside of Docker during testing
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@db:5432/housing_db"
)


# The engine is the core interface to the database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal will be used to create an independent database session for each incoming web request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the foundational class we will inherit from to create our database models
Base = declarative_base()

def get_db():
    """Dependency to yield a database session."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()