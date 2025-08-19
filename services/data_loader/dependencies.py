# services/data_loader/dependencies.py
import os

from .dal import DataLoader

# Read configuration from environment variables in a central place.
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "mydatabase")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "data")

# Build the MongoDB Connection URI.
# If a username and password are provided, build a URI with authentication (for OpenShift).
# Otherwise, build a simpler URI for local, unauthenticated development.
if MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# Create a single, shared instance (Singleton) of the DataLoader.
# All other parts of the application will import this instance to interact with the database.
data_loader = DataLoader(
    mongo_uri=MONGO_URI, db_name=MONGO_DB_NAME, collection_name=MONGO_COLLECTION_NAME
)
