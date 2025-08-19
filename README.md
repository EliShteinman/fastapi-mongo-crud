# FastAPI MongoDB CRUD Service for OpenShift

## Overview

This project is a robust, production-ready RESTful API for managing a "soldiers" database, built with Python FastAPI and MongoDB. Designed for cloud-native deployment on OpenShift, it serves as a comprehensive template for developing and deploying modern microservices, adhering to best practices in software architecture and infrastructure as code.

The entire infrastructure is defined using declarative Kubernetes manifests and can be deployed automatically with dedicated, cross-platform scripts.

### Features & Best Practices Implemented

-   **Full CRUD RESTful API:** Provides complete Create, Read, Update, and Delete (CRUD) functionality for the "soldiers" data model, adhering to REST principles.
-   **Modular API Architecture:** Uses FastAPI's `APIRouter` and a dependency injection pattern to keep API logic clean, organized, and scalable.
-   **Asynchronous DAL:** Implements a high-performance, asynchronous Data Access Layer (DAL) using `pymongo`'s async capabilities, which manages a connection pool for non-blocking database operations.
-   **Declarative Infrastructure (IaC):** All OpenShift/Kubernetes resources are defined in standardized YAML manifests located in the `infrastructure/k8s` directory.
-   **Dual Deployment Strategies:** Provides manifests for deploying MongoDB using both a standard `Deployment` and an advanced `StatefulSet` (the recommended approach for stateful applications).
-   **Advanced Configuration Management:** Employs a clear separation between non-sensitive configuration (`ConfigMap`) and sensitive data like passwords (`Secret`).
-   **Reliability & Health Monitoring:** Includes **liveness and readiness probes** for both the API and the database to ensure high availability and automated recovery.
-   **Resource Management:** Defines CPU and memory `requests` and `limits` to guarantee performance and prevent resource starvation within the cluster.
-   **Full Automation:** Provides cross-platform deployment scripts (`.sh` for Linux/macOS and `.bat` for Windows) for a complete, one-command setup.
-   **End-to-End Testing:** Includes an automated test script (`run_api_tests.sh`) to validate the deployed API's functionality.

---

## Project Structure & Documentation

The project is organized into distinct directories, each with its own detailed documentation (in Hebrew).

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
│   ├── demo_guide.md       # ➡️ Step-by-step manual deployment & usage guide
│   └── run_api_tests.sh    # E2E test script for the API
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md               # This file
```

### Navigating the Documentation

-   To understand the **Python code architecture**, read the **[Python Architecture Guide](./services/data_loader/README.md)**.
-   To understand the **Kubernetes/OpenShift resources**, read the **[Infrastructure Manifests Guide](./infrastructure/k8s/README.md)**.
-   For a **step-by-step manual deployment and testing guide**, follow the **[Manual Deployment & Usage Guide](./scripts/demo_guide.md)**.

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

## Manual Deployment & API Testing

For detailed, step-by-step instructions on how to deploy the application manually and test the API endpoints using `curl`, please refer to the **[Manual Deployment & Usage Guide](./scripts/demo_guide.md)**.