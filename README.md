# FastAPI MongoDB CRUD Service for OpenShift

🌍 **Language:** **[English](README.md)** | [עברית](README.he.md)

## Overview

This project is a robust, production-ready RESTful API for managing a "soldiers" database, built with Python FastAPI and MongoDB. Designed for cloud-native deployment on OpenShift, it serves as a comprehensive template for developing and deploying modern microservices, adhering to best practices in software architecture and infrastructure as code.

The entire infrastructure is defined using declarative Kubernetes manifests and can be deployed automatically with dedicated, cross-platform scripts.

### Features & Best Practices Implemented

-   **Full CRUD RESTful API:** Provides complete Create, Read, Update, and Delete (CRUD) functionality for the "soldiers" data model, adhering to REST principles.
-   **Modular API Architecture:** Uses FastAPI's `APIRouter` and a dependency injection pattern to keep API logic clean, organized, and scalable.
-   **Asynchronous DAL:** Implements a high-performance, asynchronous Data Access Layer (DAL) using `pymongo`'s async capabilities, which manages a connection pool for non-blocking database operations.
-   **Comprehensive Logging:** Structured logging throughout the application with configurable log levels via environment variables.
-   **Advanced Error Handling:** Multi-layered exception handling with proper HTTP status codes and detailed error messages.
-   **Input Validation:** Helper functions to prevent code duplication and ensure consistent validation across endpoints.
-   **Health Monitoring:** Dual health check endpoints - basic liveness checks and detailed readiness checks with database connectivity verification.
-   **Declarative Infrastructure (IaC):** All OpenShift/Kubernetes resources are defined in standardized YAML manifests located in the `infrastructure/k8s` directory.
-   **Dual Deployment Strategies:** Provides manifests for deploying MongoDB using both a standard `Deployment` and an advanced `StatefulSet` (the recommended approach for stateful applications).
-   **Advanced Configuration Management:** Employs a clear separation between non-sensitive configuration (`ConfigMap`) and sensitive data like passwords (`Secret`).
-   **Reliability & Health Monitoring:** Includes **liveness and readiness probes** for both the API and the database to ensure high availability and automated recovery.
-   **Resource Management:** Defines CPU and memory `requests` and `limits` to guarantee performance and prevent resource starvation within the cluster.
-   **Full Automation:** Provides cross-platform deployment scripts (`.sh` for Linux/macOS and `.bat` for Windows) for a complete, one-command setup.
-   **End-to-End Testing:** Includes an automated test script (`run_api_tests.sh`) to validate the deployed API's functionality.

---

## Project Structure & Documentation

The project is organized into distinct directories, each with its own detailed documentation.

```
.
├── infrastructure/
│   └── k8s/
│       ├── README.md   # ➡️ In-depth explanation of all YAML manifests
│       └── ...         # All Kubernetes/OpenShift YAML manifests
├── services/
│   └── data_loader/
│       ├── crud/
│       │   └── soldiers.py # APIRouter for CRUD operations
│       ├── dal.py          # Data Access Layer (DAL)
│       ├── dependencies.py # Configuration and dependency management
│       ├── main.py         # Main FastAPI application entrypoint
│       ├── models.py       # Pydantic data models
│       └── README.md       # ➡️ In-depth explanation of the Python code architecture
├── scripts/
│   ├── deploy.sh           # Automated deployment script (Deployment strategy)
│   ├── deploy.bat          # Windows version
│   ├── deploy-statefulset.sh # Automated deployment script (StatefulSet strategy)
│   ├── deploy-statefulset.bat# Windows version
│   ├── README.md           # ➡️ Scripts overview and quick start
│   ├── demo_guide.md       # ➡️ Step-by-step manual deployment & usage guide
│   └── run_api_tests.sh    # E2E test script for the API
├── example.env             # Environment variables template for local development
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md               # This file
```

### Navigating the Documentation

-   **🚀 Quick Start:** Use the automated scripts in **[scripts/](./scripts/)**
-   **📚 Complete Manual Guide:** Follow the **[Manual Deployment & Usage Guide](scripts/demo_guide.md)** for step-by-step instructions
-   **⚙️ Python Architecture:** Read the **[Python Architecture Guide](services/data_loader/README.md)** to understand the code structure
-   **🔧 Infrastructure Details:** Read the **[Infrastructure Manifests Guide](infrastructure/k8s/README.md)** to understand the Kubernetes/OpenShift resources

---

## Local Development

### Environment Setup
1. **Copy environment template:**
   ```bash
   cp example.env .env
   ```

2. **For local development, the default values work as-is** (MongoDB without authentication)

3. **Optional: Adjust log level in .env:**
   ```bash
   LOG_LEVEL=DEBUG  # For detailed logs
   LOG_LEVEL=INFO   # Default
   LOG_LEVEL=ERROR  # Minimal logs
   ```

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run local MongoDB (using Docker)
docker run -d -p 27017:27017 --name local-mongo mongo:8.0

# Start the application
uvicorn services.data_loader.main:app --reload --port 8000
```

### Local API Access
- **Application:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## Automated Deployment

For a quick setup, use the provided automation scripts.

### Prerequisites

1.  Access to an OpenShift cluster and the `oc` CLI tool.
2.  A Docker Hub account and credentials (`docker login`).
3.  A running Docker daemon (e.g., Docker Desktop).
4.  `git` installed for version tracking.

### Instructions

The `scripts` directory contains automated deployment files. Run the appropriate script from the project's **root directory**, providing your Docker Hub username as the first argument.

#### Strategy 1: Standard Deployment
This approach uses a standard Kubernetes `Deployment` for MongoDB.

*   **For Linux / macOS:**
    ```bash
    chmod +x ./scripts/deploy.sh
    ./scripts/deploy.sh your-dockerhub-username
    ```

*   **For Windows:**
    ```batch
    .\scripts\deploy.bat your-dockerhub-username
    ```

#### Strategy 2: StatefulSet Deployment
This approach uses a Kubernetes `StatefulSet`, which is the recommended practice for stateful applications like databases.

*   **For Linux / macOS:**
    ```bash
    chmod +x ./scripts/deploy-statefulset.sh
    ./scripts/deploy-statefulset.sh your-dockerhub-username
    ```

*   **For Windows:**
    ```batch
    .\scripts\deploy-statefulset.bat your-dockerhub-username
    ```

The script will automatically build the Docker image, push it to Docker Hub, deploy all necessary resources to your OpenShift project, and print the final application URL.

---

## API Testing

### Getting Your Application URL
First, get the public URL of your deployed application:

**For Deployment strategy:**
```bash
export API_URL="https://$(oc get route mongo-api-route -o jsonpath='{.spec.host}')"
echo "Application URL: ${API_URL}"
```

**For StatefulSet strategy:**
```bash
export API_URL="https://$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')"
echo "Application URL: ${API_URL}"
```

### Automated Testing
Use the provided test script for comprehensive API validation:

```bash
# Run the automated test suite
./scripts/run_api_tests.sh "${API_URL}"
```

The test script will automatically:
- Test all CRUD operations
- Validate error handling
- Check data persistence
- Verify API responses
- Clean up test data

### Manual Testing Examples
For quick manual tests:

```bash
# Check if the API is running
curl "${API_URL}/health"

# View API documentation
echo "API Documentation: ${API_URL}/docs"
```

---

## Manual Deployment & API Testing

For detailed, step-by-step instructions on how to deploy the application manually and test the API endpoints using `curl`, please refer to the **[Manual Deployment & Usage Guide](scripts/demo_guide.md)**.