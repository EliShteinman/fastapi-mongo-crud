# services/data_loader/crud/soldiers.py
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

# Import the Pydantic models and the shared DAL instance
from .. import models
from ..dependencies import data_loader

logger = logging.getLogger(__name__)

# Create an APIRouter instance. Think of it as a "mini-FastAPI" application.
router = APIRouter(
    prefix="/soldiersdb",  # All paths in this router will be prefixed with /soldiersdb
    tags=[
        "Soldiers CRUD"
    ],  # Group these endpoints under "Soldiers CRUD" in the Swagger UI docs
)


# --- Helper Functions ---
def validate_soldier_id(soldier_id: int):
    """Validates that soldier_id is a positive integer."""
    if soldier_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Soldier ID must be a positive integer",
        )


# --- CREATE ---
@router.post(
    "/", response_model=models.SoldierInDB, status_code=status.HTTP_201_CREATED
)
async def create_soldier(soldier: models.SoldierCreate):
    """
    Creates a new soldier in the database.
    """
    try:
        logger.info(f"Attempting to create soldier with ID {soldier.ID}")
        created_soldier = await data_loader.create_item(soldier)
        logger.info(f"Successfully created soldier with ID {soldier.ID}")
        return created_soldier
    except ValueError as e:
        # Catch the duplicate ID error from the DAL and convert it to a 409 Conflict response
        logger.warning(f"Conflict creating soldier with ID {soldier.ID}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        # Catch a database connection error from the DAL and convert it to a 503 Service Unavailable response
        logger.error(f"Database error creating soldier: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except ValidationError as e:
        # Catch Pydantic validation errors
        logger.warning(f"Validation error creating soldier: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error creating soldier: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


# --- READ (All) ---
@router.get("/", response_model=List[models.SoldierInDB])
async def read_all_soldiers():
    """
    Retrieves all soldiers from the database.
    """
    try:
        logger.info("Attempting to retrieve all soldiers")
        soldiers = await data_loader.get_all_data()
        logger.info(f"Successfully retrieved {len(soldiers)} soldiers")
        return soldiers
    except RuntimeError as e:
        logger.error(f"Database error retrieving all soldiers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving all soldiers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


# --- READ (Single) ---
@router.get("/{soldier_id}", response_model=models.SoldierInDB)
async def read_soldier_by_id(soldier_id: int):
    """
    Retrieves a single soldier by their numeric ID.
    """
    validate_soldier_id(soldier_id)

    try:
        logger.info(f"Attempting to retrieve soldier with ID {soldier_id}")
        soldier = await data_loader.get_item_by_id(soldier_id)
        if soldier is None:
            logger.info(f"Soldier with ID {soldier_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found",
            )
        logger.info(f"Successfully retrieved soldier with ID {soldier_id}")
        return soldier
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except RuntimeError as e:
        logger.error(f"Database error retrieving soldier {soldier_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving soldier {soldier_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


# --- UPDATE ---
@router.put("/{soldier_id}", response_model=models.SoldierInDB)
async def update_soldier(soldier_id: int, soldier_update: models.SoldierUpdate):
    """
    Updates an existing soldier by their numeric ID.
    """
    validate_soldier_id(soldier_id)

    try:
        logger.info(f"Attempting to update soldier with ID {soldier_id}")
        updated_soldier = await data_loader.update_item(soldier_id, soldier_update)
        if updated_soldier is None:
            logger.info(f"Soldier with ID {soldier_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found to update",
            )
        logger.info(f"Successfully updated soldier with ID {soldier_id}")
        return updated_soldier
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as e:
        logger.warning(f"Validation error updating soldier {soldier_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Database error updating soldier {soldier_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error updating soldier {soldier_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


# --- DELETE ---
@router.delete("/{soldier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_soldier(soldier_id: int):
    """
    Deletes an existing soldier by their numeric ID.
    """
    validate_soldier_id(soldier_id)

    try:
        logger.info(f"Attempting to delete soldier with ID {soldier_id}")
        success = await data_loader.delete_item(soldier_id)
        if not success:
            logger.info(f"Soldier with ID {soldier_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found to delete",
            )
        logger.info(f"Successfully deleted soldier with ID {soldier_id}")
        # On successful deletion with a 204 status, no response body is returned.
        return
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except RuntimeError as e:
        logger.error(f"Database error deleting soldier {soldier_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting soldier {soldier_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
