from fastapi import FastAPI

# Initialise the FastAPI application
app = FastAPI(
    title="UK Housing Market API",
    description="An API providing insights and data on the UK housing market.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    """
    Root endpoint to check if the API is running successfully.
    """
    return {"message": "Welcome to the UK Housing Market API", "status": "Operational"}