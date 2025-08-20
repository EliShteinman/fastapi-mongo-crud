# services/data_loader/main.py
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from .crud import soldiers
from .dependencies import data_loader

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    # On server startup:
    logger.info("Application startup: connecting to database...")
    try:
        await data_loader.connect()
        logger.info("Database connection established successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")

    yield

    # On server shutdown:
    logger.info("Application shutdown: disconnecting from database...")
    try:
        data_loader.disconnect()
        logger.info("Database disconnection completed.")
    except Exception as e:
        logger.error(f"Error during database disconnection: {e}")


# Create the main FastAPI application instance
app = FastAPI(
    lifespan=lifespan,
    title="FastAPI MongoDB CRUD Service",
    version="2.0",
    description="A microservice for managing soldier data, deployed on OpenShift.",
)

# Include the CRUD router from the 'soldiers' module.
# This makes all endpoints defined in that router available under the main app.
app.include_router(soldiers.router)


@app.get("/")
def health_check_endpoint():
    """
    Health check endpoint.
    Used by OpenShift's readiness and liveness probes.
    """
    return {"status": "ok", "service": "FastAPI MongoDB CRUD Service"}


@app.get("/health")
def detailed_health_check():
    """
    Detailed health check endpoint.
    Returns 503 if database is not available.
    """
    db_status = "connected" if data_loader.collection is not None else "disconnected"

    if db_status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    return {
        "status": "ok",
        "service": "FastAPI MongoDB CRUD Service",
        "version": "2.0",
        "database_status": db_status,
    }
