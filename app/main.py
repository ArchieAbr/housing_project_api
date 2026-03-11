import os
from contextlib import asynccontextmanager
from azure.monitor.opentelemetry import configure_azure_monitor
configure_azure_monitor()
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from alembic.config import Config
from alembic import command
from . import models, db
from .routers import listings, analytics
from .exceptions import CustomAPIException
from .seed import seed_database_if_empty


def run_migrations():
    """Run Alembic migrations to ensure database schema is up to date."""
    try:
        # Get the directory where this file lives
        app_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_ini_path = os.path.join(app_dir, "alembic.ini")
        
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", os.path.join(app_dir, "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", db.SQLALCHEMY_DATABASE_URL)
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully.")
    except Exception as e:
        print(f"Error running migrations: {e}")
        # Fallback to create_all if Alembic fails
        models.Base.metadata.create_all(bind=db.engine)
        print("Fallback: Created tables using SQLAlchemy create_all.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application."""
    # Startup: Run migrations and seed data if empty
    run_migrations()
    seed_database_if_empty()
    yield
    # Shutdown: Nothing to clean up


app = FastAPI(
    title="UK Housing Market API",
    description="An API providing insights and data on the UK housing market.",
    version="1.0.0",
    lifespan=lifespan
)

# Global Exception Handler
@app.exception_handler(CustomAPIException)
async def custom_api_exception_handler(request: Request, exc: CustomAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.name, "message": exc.detail},
    )

# Register modular routers
app.include_router(listings.router)
app.include_router(analytics.router)