# services/data_loader/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .crud import soldiers
from .dependencies import data_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    # On server startup:
    print("Application startup: connecting to database...")
    await data_loader.connect()
    yield
    # On server shutdown:
    print("Application shutdown: disconnecting from database...")
    data_loader.disconnect()


# Create the main FastAPI application instance
app = FastAPI(
    lifespan=lifespan,
    title="FastAPI MongoDB CRUD Service",
    version="2.0",
    description="A microservice for managing soldier data, deployed on OpenShift.",
)

# Include the CRUD router from the 'items' module.
# This makes all endpoints defined in that router available under the main app.
app.include_router(soldiers.router)


@app.get("/")
def health_check_endpoint():
    """
    Health check endpoint.
    Used by OpenShift's readiness and liveness probes.
    """
    return {"status": "ok"}
