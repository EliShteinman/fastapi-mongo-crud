# FastAPI MongoDB CRUD Service for OpenShift

## Overview

This project provides a robust, production-ready template for deploying a Python FastAPI application with a MongoDB backend on OpenShift. Originating as a simple data-fetching assignment, this project has been significantly expanded to showcase a complete, best-practice architecture for building and deploying cloud-native microservices.

The entire infrastructure is defined using declarative Kubernetes manifests and can be deployed automatically with dedicated, cross-platform scripts.

### Features & Best Practices Implemented

-   **Full CRUD API:** The API was extended from a single `GET` endpoint to full Create, Read, Update, and Delete functionality for a "soldiers" database.
-   **Modular API Architecture:** Uses FastAPI's `APIRouter` and a dependency injection pattern to keep API logic clean, organized, and scalable.
-   **Asynchronous DAL:** Implements a high-performance, asynchronous Data Access Layer (DAL) using `motor` (via `pymongo`), which manages a connection pool to MongoDB.
-   **Declarative Infrastructure (IaC):** All OpenShift/Kubernetes resources are defined in standardized YAML manifests located in the `infrastructure/k8s` directory.
-   **Dual Deployment Strategies:** Provides manifests for deploying MongoDB using both a standard `Deployment` and an advanced `StatefulSet` for persistent, stateful applications.
-   **Advanced Configuration Management:** Clear separation between non-sensitive configuration (`ConfigMap`) and sensitive data (`Secret`).
-   **Reliability & Health Monitoring:** Includes **liveness and readiness probes** for both the API and the database to ensure high availability.
-   **Resource Management:** Defines CPU and memory `requests` and `limits` to guarantee performance and prevent resource starvation in the cluster.
-   **Full Automation:** Provides cross-platform deployment scripts (`.sh` and `.bat`) for a complete, one-command setup for both deployment strategies.
-   **End-to-End Testing:** Includes an automated test script (`run_api_tests.sh`) to validate the deployed API's functionality.

---

## Project Structure & Documentation

The project is organized into distinct directories, each with its own detailed documentation.

```
.
├── infrastructure/
│   └── k8s/
│       ├── README.md   # ➡️ (Hebrew) In-depth explanation of all YAML manifests
│       └── ...         # All Kubernetes/OpenShift YAML manifests
├── services/
│   └── data_loader/
│       ├── crud/
│       │   └── soldiers.py # APIRouter for CRUD operations
│       ├── dal.py          # Data Access Layer (DAL)
│       ├── dependencies.py # Configuration and dependency management
│       ├── main.py         # Main FastAPI application entrypoint
│       ├── models.py       # Pydantic data models
│       └── README.md       # ➡️ (Hebrew) In-depth explanation of the Python code architecture
├── scripts/
│   ├── deploy.sh           # Automated deployment script (Deployment strategy)
│   ├── deploy.bat          # Windows version
│   ├── deploy-statefulset.sh # Automated deployment script (StatefulSet strategy)
│   ├── deploy-statefulset.bat# Windows version
│   └── run_api_tests.sh    # E2E test script for the API
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md               # This file
```

### Navigating the Documentation

-   To understand the **Python code architecture**, read the **[Python Architecture Guide (Hebrew)](./services/data_loader/README.md)**.
-   To understand the **Kubernetes/OpenShift resources**, read the **[Infrastructure Manifests Guide (Hebrew)](./infrastructure/k8s/README.md)**.
-   For a **step-by-step manual deployment tutorial**, follow the **[Manual Deployment & Usage Guide (Hebrew)](./demo_guide.md)**.

---

## Automated Deployment

For a quick setup, use the provided automation scripts.

### Prerequisites

1.  Access to an OpenShift cluster and the `oc` CLI.
2.  A Docker Hub account (`docker login` executed).
3.  Docker Desktop (or Docker daemon) running.
4.  `git` installed and configured.

### Instructions

Run the appropriate script for your desired deployment strategy, providing your Docker Hub username as the first argument.

#### Standard Deployment
```bash
# For Linux / macOS
chmod +x deploy.sh
./deploy.sh your-dockerhub-username

# For Windows
.\deploy.bat your-dockerhub-username
```

#### StatefulSet Deployment
```bash
# For Linux / macOS
chmod +x deploy-statefulset.sh
./deploy-statefulset.sh your-dockerhub-username

# For Windows
.\deploy-statefulset.bat your-dockerhub-username
```
The script will build the image, push it to Docker Hub, deploy all resources to OpenShift, and print the final application URL.

---

## Manual Deployment & API Testing

For detailed, step-by-step instructions on how to deploy the application manually and test the API endpoints using `curl`, please refer to the **[Manual Deployment & Usage Guide](./demo_guide.md)**.