# services/data_loader/models.py
from typing import Optional

from pydantic import BaseModel, Field

# A Type Alias to clarify that in our code, MongoDB's special ObjectId
# will be treated as a string.
PyObjectId = str

# --------------------------------------------------------------------------
# --- Pydantic Models for the CRUD API ---
# These models define the data shapes for validation and serialization.
# --------------------------------------------------------------------------


class SoldierBase(BaseModel):
    """
    Base model containing fields that are common to all soldier variants
    and are provided by the user.
    """

    first_name: str
    last_name: str
    phone_number: int
    rank: str


class SoldierCreate(SoldierBase):
    """
    Model used to receive data from the user when creating a new soldier (in a POST request).
    It inherits all fields from SoldierBase and adds the mandatory numeric ID.
    """

    ID: int


class SoldierUpdate(BaseModel):
    """
    Model used to receive data for updating an existing soldier (in a PUT/PATCH request).
    All fields are optional to allow for partial updates.
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[int] = None
    rank: Optional[str] = None


class SoldierInDB(SoldierBase):
    """
    Model representing a complete soldier object as it exists in the database
    and as it will be returned from the API.
    It includes all fields, including system-managed ones like the MongoDB '_id'.
    """

    # The `alias` parameter in Field() bridges the gap between the MongoDB field name ('_id')
    # and the field name we want to expose in our API ('id').
    id: PyObjectId = Field(alias="_id")
    ID: int  # Our application-specific numeric ID

    class Config:
        # Allows Pydantic to create a model instance from object attributes (e.g., db_result.id)
        # and not just from dictionaries. Also known as ORM mode.
        from_attributes = True

        # Allows populating the model using either the field name ('id') or its alias ('_id').
        populate_by_name = True
