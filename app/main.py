from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from . import models, db
from .routers import listings, analytics
from .exceptions import CustomAPIException
from .seed import seed_database_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application."""
    # Startup: Create tables and seed data if empty
    models.Base.metadata.create_all(bind=db.engine)
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