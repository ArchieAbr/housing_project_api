from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from . import models, db
from .routers import listings, analytics

models.Base.metadata.create_all(bind=db.engine)

app = FastAPI(
    title="UK Housing Market API",
    description="An API providing insights and data on the UK housing market.",
    version="1.0.0"
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