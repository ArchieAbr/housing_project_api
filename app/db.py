import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Fetch the database URL from environment variables
# Local Docker: DATABASE_URL not set, uses fallback
# Azure: Set DATABASE_URL in App Service Configuration
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@db:5432/housing_db"
)

# Azure PostgreSQL requires SSL - add sslmode if connecting to Azure
connect_args = {}
if "azure" in SQLALCHEMY_DATABASE_URL.lower():
    # Ensure sslmode is set for Azure connections
    if "sslmode" not in SQLALCHEMY_DATABASE_URL:
        SQLALCHEMY_DATABASE_URL += "?sslmode=require"
    connect_args = {"connect_timeout": 30}

# The engine is the core interface to the database
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

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