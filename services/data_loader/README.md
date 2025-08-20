# Technical Guide: Python Code Architecture

🌍 **Language:** **[English](README.md)** | [עברית](README.he.md)

This document provides a technical analysis, file by file and line by line, of the FastAPI application for managing soldier data. The goal is to explain the role of each component, data flow, and the logic behind the code structure.

## Overall Architecture

The application is built in a modular architecture to ensure separation of concerns. The general flow is:

`main.py` (entry point) → `crud/soldiers.py` (API layer) → `dependencies.py` (creates DAL) → `dal.py` (data access layer)

## File Structure
```
data_loader/
├── crud/
│   └── soldiers.py    # API endpoints
├── dal.py            # Data Access Layer
├── dependencies.py   # Configuration and dependency management
├── main.py          # Main entry point
└── models.py        # Data models (Pydantic)
```

---

## 1. `dependencies.py` - Configuration and Dependencies Hub

This file is the first to execute in practice, and its role is to prepare the shared components for the application.

```python
# Lines 1-2: Import required tools.
# 'os' for reading environment variables, and 'DataLoader' from our dal file.
import os
from .dal import DataLoader

# Lines 7-12: Collecting configuration from the runtime environment.
# Each parameter is read from an environment variable using os.getenv().
# If the variable doesn't exist (e.g., in local development), a default value is provided.
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")           # Server address
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))           # Port (converted to number)
MONGO_USER = os.getenv("MONGO_USER", "")                   # Username (empty if undefined)
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")           # Password (empty if undefined)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "mydatabase")   # Database name
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "data")  # Collection name

# Lines 17-20: Building the connection string (Connection String URI).
# The code checks if username and password were provided.
# If yes - builds URI with authentication (suitable for OpenShift with credentials)
# If no - builds simple URI (suitable for local MongoDB without authentication)
if MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# Lines 24-26: ★ Creating a single instance (Singleton) of DataLoader ★
# This line runs only once when the application starts.
# We "inject" the configuration we collected into the DataLoader class.
# The 'data_loader' variable is then imported everywhere that needs database access.
data_loader = DataLoader(
    mongo_uri=MONGO_URI, 
    db_name=MONGO_DB_NAME, 
    collection_name=MONGO_COLLECTION_NAME
)
```

---

## 2. `models.py` - Data Models (Schema)

This file defines the data "shapes" using Pydantic. It serves as a "contract" for the API.

```python
# Line 8: 'PyObjectId = str' is a type alias.
# It helps us remember that in code, MongoDB's ObjectId is handled as a string.
PyObjectId = str

# Lines 16-25: SoldierBase defines the basic fields common to all soldiers.
# Every soldier must include: first name, last name, phone, and rank.
class SoldierBase(BaseModel):
    first_name: str      # First name
    last_name: str       # Last name
    phone_number: int    # Phone number
    rank: str           # Military rank

# Lines 28-34: SoldierCreate inherits from SoldierBase and adds ID field.
# This model is used for validation of input in soldier creation requests (POST).
class SoldierCreate(SoldierBase):
    ID: int             # Unique soldier identifier (integer)

# Lines 37-46: SoldierUpdate allows partial updates of soldier data.
# All fields are optional - you can update only some of the data.
class SoldierUpdate(BaseModel):
    first_name: Optional[str] = None     # First name (optional)
    last_name: Optional[str] = None      # Last name (optional)
    phone_number: Optional[int] = None   # Phone number (optional)
    rank: Optional[str] = None          # Rank (optional)

# Lines 49-64: SoldierInDB is the complete model for a soldier returned from database.
class SoldierInDB(SoldierBase):
    # Line 58: ★ The critical part ★
    # 'id: PyObjectId = Field(alias="_id")' creates mapping between fields:
    # In incoming data from MongoDB look for '_id', and in outgoing JSON create 'id' field
    id: PyObjectId = Field(alias="_id")  # MongoDB ObjectId as string
    ID: int                              # Our numeric identifier

    class Config:
        # Line 64: Allows creating model from objects (not just dictionaries)
        from_attributes = True
        # Line 67: Allows alias to work in both directions (_id ↔ id)
        populate_by_name = True
```

---

## 3. `dal.py` - Data Access Layer

This file contains all the logic for communicating with MongoDB. It includes comprehensive logging for monitoring and troubleshooting.

```python
# Lines 2-11: Import all tools needed for MongoDB, data handling, and logging
import logging
from bson import ObjectId                    # For handling MongoDB ObjectId
from pymongo import AsyncMongoClient         # Asynchronous client
from pymongo.errors import DuplicateKeyError, PyMongoError  # Error handling
from .models import SoldierCreate, SoldierUpdate           # Our models

# Lines 13-14: Set up logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lines 17-30: Define DataLoader class - our MongoDB expert
class DataLoader:
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        # Store connection details received from dependencies.py
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        # Initialize all connections to None - will get values only after successful connection
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

# Lines 32-48: Connection method - the heart of the system with detailed logging
async def connect(self):
    try:
        # Lines 35-36: Create connection with 5-second timeout
        self.client = AsyncMongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
        # Line 38: Send 'ping' to verify connection is working (await = wait for response)
        await self.client.admin.command("ping")
        # Lines 39-40: Get access to database and collection
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        # Add logging for successful connection
        logger.info("Successfully connected to MongoDB.")
        # Line 42: Set up unique index on ID field
        await self._setup_indexes()
    except PyMongoError as e:
        # Add logging for connection failure
        logger.error(f"DATABASE CONNECTION FAILED: {e}")
        self.client = None
        self.db = None
        self.collection = None

# Lines 49-56: Set up unique index with logging
async def _setup_indexes(self):
    if self.collection is not None:
        try:
            # Create unique index on 'ID' field - prevents inserting duplicate IDs
            await self.collection.create_index("ID", unique=True)
            logger.info("Unique index on 'ID' field ensured.")
        except PyMongoError as e:
            logger.error(f"Failed to create index: {e}")

# Lines 64-78: Read all soldiers from database with logging and improved error handling
async def get_all_data(self) -> List[Dict[str, Any]]:
    # Critical check - if connection failed, self.collection will be None
    if self.collection is None:
        raise RuntimeError("Database connection is not available.")
    
    try:
        items: List[Dict[str, Any]] = []
        # 'async for' - asynchronous loop that pulls documents one by one
        async for item in self.collection.find({}):  # {} = all documents
            # Convert ObjectId to string (JSON doesn't know what ObjectId is)
            item["_id"] = str(item["_id"])
            items.append(item)
        # Log successful operation
        logger.info(f"Retrieved {len(items)} soldiers from database.")
        return items
    except PyMongoError as e:
        # Logging and error handling
        logger.error(f"Error retrieving all data: {e}")
        raise RuntimeError(f"Database operation failed: {e}")
```

**Logging and Error Handling Improvements:**
- Every operation is logged with appropriate severity level
- Errors are logged with full details
- Successes are logged for performance tracking
- Every MongoDB exception is caught and translated to clear error
- All logging provides context for debugging

---

## 4. `crud/soldiers.py` - API Layer with Helper Functions and Comprehensive Logging

This file defines the API endpoints and contains HTTP logic. It includes significant improvements in error handling and code duplication prevention.

```python
# Lines 2-10: Import tools from FastAPI, logging, and models
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from .. import models
from ..dependencies import data_loader  # Shared DataLoader instance

# Line 12: Create dedicated logger for this module
logger = logging.getLogger(__name__)

# Lines 15-20: Create APIRouter
router = APIRouter(
    prefix="/soldiersdb",        # All URLs here will start with /soldiersdb
    tags=["Soldiers CRUD"],      # Group in Swagger documentation
)

# Helper function to prevent code duplication
# Lines 24-30: Function that validates soldier_id
def validate_soldier_id(soldier_id: int):
    """Validates that soldier_id is a positive integer."""
    if soldier_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Soldier ID must be a positive integer",
        )
```

**The helper function prevents repeating this code in every endpoint:**
```python
# Instead of repeating this in every function:
if soldier_id <= 0:
    raise HTTPException(status_code=422, detail="ID must be positive")

# Now simply call:
validate_soldier_id(soldier_id)
```

**Error Handling and Logging Improvements:**

```python
# Example from create_soldier (lines 37-68):
async def create_soldier(soldier: models.SoldierCreate):
    try:
        # Log operation start
        logger.info(f"Attempting to create soldier with ID {soldier.ID}")
        created_soldier = await data_loader.create_item(soldier)
        # Log success
        logger.info(f"Successfully created soldier with ID {soldier.ID}")
        return created_soldier
    except ValueError as e:
        # Handle duplicate ID error
        logger.warning(f"Conflict creating soldier with ID {soldier.ID}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        # Handle database connection error
        logger.error(f"Database error creating soldier: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ValidationError as e:
        # Handle Pydantic validation errors
        logger.warning(f"Validation error creating soldier: {str(e)}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error creating soldier: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail="An unexpected error occurred")
```

**Using the helper function:**
```python
# In every endpoint that receives soldier_id (lines 101, 136, 176):
@router.get("/{soldier_id}")
async def read_soldier_by_id(soldier_id: int):
    validate_soldier_id(soldier_id)  # Call helper function
    # Rest of code...
```

---

## 5. `main.py` - Application Assembly with Advanced Lifecycle Management

The main file that connects all parts and creates the complete FastAPI application, including advanced logging management and health checks.

```python
# Lines 2-9: Import required tools including logging and os
from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI, HTTPException, status
from .crud import soldiers              # Router we created
from .dependencies import data_loader   # Shared DataLoader instance

# Read logging level from environment variables
# Lines 11-14: Set up dynamic logging based on environment variables
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# Lifecycle management with error handling
# Lines 17-38: Application lifecycle management with logging
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code before 'yield' runs at server startup
    logger.info("Application startup: connecting to database...")
    try:
        await data_loader.connect()  # Connect to database
        logger.info("Database connection established successfully.")
    except Exception as e:
        # Don't throw exception - let application start
        logger.error(f"Failed to connect to database: {e}")
    
    yield                        # Here the server runs and receives requests...
    
    # Code after 'yield' runs at server shutdown
    logger.info("Application shutdown: disconnecting from database...")
    try:
        data_loader.disconnect()     # Disconnect from database
        logger.info("Database disconnection completed.")
    except Exception as e:
        logger.error(f"Error during database disconnection: {e}")
```

**Health Check Improvements:**

```python
# Lines 54-60: Basic health check (for liveness probe)
@app.get("/")
def health_check_endpoint():
    """Basic health check - used by OpenShift liveness probe"""
    return {"status": "ok", "service": "FastAPI MongoDB CRUD Service"}

# Advanced health check (for readiness probe)
# Lines 63-82: Detailed health check with database verification
@app.get("/health")
def detailed_health_check():
    """Detailed health check that verifies database connectivity"""
    db_status = "connected" if data_loader.collection is not None else "disconnected"
    
    # Throw error if database is not available
    if db_status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    
    return {
        "status": "ok",
        "service": "FastAPI MongoDB CRUD Service",
        "version": "2.0",
        "database_status": db_status
    }
```

**Difference between Health Checks:**
- **`/`** - Simple check that server is alive (liveness probe)
- **`/health`** - Detailed check including database (readiness probe)

---

## Complete Data Flow Example with Logging

When a user sends a `POST /soldiersdb/` request to create a new soldier:

1. **FastAPI receives the request** and routes it to `soldiers.router`
2. **The router calls** `create_soldier()` in `crud/soldiers.py`
3. **Log operation start:** `logger.info(f"Attempting to create soldier with ID {soldier.ID}")`
4. **The function validates** the data using `SoldierCreate`
5. **Call to DAL:** `await data_loader.create_item(soldier)`
6. **DAL connects to MongoDB** and inserts document with logging
7. **Document returns from database** with `_id` added automatically
8. **Log success:** `logger.info(f"Successfully created soldier with ID {soldier.ID}")`
9. **Convert ObjectId** to string in DAL
10. **Return result** through router to FastAPI
11. **FastAPI serializes** using `SoldierInDB`
12. **Return JSON** to client with status code 201

## Architectural Principles

### Separation of Concerns
- **models.py**: Only data definitions
- **dal.py**: Only database logic + logging
- **crud/soldiers.py**: Only HTTP/API logic + validation helpers + logging
- **main.py**: Only assembly, configuration, and lifecycle management + logging
- **dependencies.py**: Only dependency management

### Multi-layered Error Handling
- Each layer handles errors at its level
- Comprehensive logging at every level
- Comprehensive exception handling with fallback to 500 errors
- Distinction between client errors (4xx) and server errors (5xx)

### Comprehensive Logging
- Logging level set from environment variables
- Every operation logged (start and completion)
- Errors logged with full details
- Performance monitoring (how many records found/created)

### External Configuration
- All settings read from environment variables
- Including dynamic logging level
- Support for different environments (local vs OpenShift)

### DRY (Don't Repeat Yourself)
- Helper functions to prevent code duplication
- Centralized validation
- Consistent error handling patterns