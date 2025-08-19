@echo off
setlocal

REM ================================================================================
REM  Deploys the FastAPI service using the advanced STATEFULSET approach.
REM ================================================================================

REM --- Step 0: Setup and Configuration ---

REM Ensure script runs from the project root directory
FOR /F "delims=" %%g IN ('git rev-parse --show-toplevel') DO (SET "PROJECT_ROOT=%%g")
IF NOT DEFINED PROJECT_ROOT (
    echo [ERROR] Could not determine project root. Ensure this is a git repository.
    exit /b 1
)
cd /d "%PROJECT_ROOT%"
echo [INFO] Running script from project root: %PROJECT_ROOT%

REM Validate input parameter (Docker Hub username)
IF "%~1"=="" (
    echo [ERROR] Docker Hub username must be provided as the first argument.
    echo [USAGE] .\scripts\deploy-statefulset.bat ^<your-dockerhub-username^>
    exit /b 1
)
SET "DOCKERHUB_USERNAME=%~1"
SET "IMAGE_NAME=fastapi-mongo-crud"

REM Create a unique image tag (from git commit or timestamp)
FOR /F "tokens=*" %%g IN ('git rev-parse --short HEAD 2^>nul') DO SET "IMAGE_TAG=%%g"
IF NOT DEFINED IMAGE_TAG (
    FOR /F "delims=" %%g IN ('powershell -NoProfile -Command "Get-Date -UFormat %%s"') DO SET "IMAGE_TAG=demo-%%g"
)
SET "FULL_IMAGE_NAME=docker.io/%DOCKERHUB_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG%"
echo [INFO] Using image: %FULL_IMAGE_NAME%

REM --- Step 1: Build and Push Docker Image ---
echo.
echo ================================================================================
echo    Step 1: Building and Pushing Docker Image
echo ================================================================================
docker buildx build --no-cache --platform linux/amd64,linux/arm64 -t "%FULL_IMAGE_NAME%" --push .
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker build failed.
    exit /b 1
)
echo [SUCCESS] Image successfully pushed to Docker Hub.

REM --- Step 2: Apply Infrastructure to OpenShift ---
echo.
echo ================================================================================
echo    Step 2: Applying Infrastructure to OpenShift
echo ================================================================================
echo [INFO] Using current OpenShift project:
oc project -q
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to get current OpenShift project. Are you logged in?
    exit /b 1
)

SET "K8S_DIR=infrastructure\k8s"

echo.
echo ---^> Deploying MongoDB (StatefulSet)...
oc apply -f %K8S_DIR%\00-mongo-configmap.yaml
oc apply -f %K8S_DIR%\01-mongo-secret.yaml
REM NOTE: A separate PVC is NOT applied. The StatefulSet manages it.
oc apply -f %K8S_DIR%\03a-mongo-statefulset.yaml
oc apply -f %K8S_DIR%\04a-mongo-headless-service.yaml

echo [INFO] Waiting for MongoDB pod to become ready...
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] MongoDB pod did not become ready. Check pod logs for errors.
    exit /b 1
)
echo [SUCCESS] MongoDB pod is ready.

echo [INFO] Allowing time for MongoDB internal initialization...
timeout /t 15 /nobreak >nul
echo [SUCCESS] MongoDB is fully initialized.

echo.
echo ---^> Deploying FastAPI Application...
powershell -NoProfile -Command "(Get-Content -Raw %K8S_DIR%\05a-fastapi-deployment-for-statefulset.yaml) -replace 'docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest', '%FULL_IMAGE_NAME%' | oc apply -f -"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to apply FastAPI deployment manifest.
    exit /b 1
)
oc apply -f %K8S_DIR%\06a-fastapi-service-for-statefulset.yaml

echo [INFO] Waiting for FastAPI pod to be ready...
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api-stateful --timeout=300s
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] FastAPI pod did not become ready. Check pod logs for errors.
    exit /b 1
)
echo [SUCCESS] FastAPI Application is ready.

echo.
echo ---^> Exposing FastAPI with a Route...
oc apply -f %K8S_DIR%\07a-fastapi-route-for-statefulset.yaml
echo [SUCCESS] Route created.

echo.
echo ================================================================================
echo    Deployment Complete!
echo ================================================================================
FOR /F "usebackq delims=" %%g IN (`oc get route mongo-api-route-stateful -o jsonpath={.spec.host}`) DO SET "ROUTE_URL=%%g"
IF NOT DEFINED ROUTE_URL (
    echo [WARNING] Could not retrieve the application URL.
) ELSE (
    echo Your application is available at: https://%ROUTE_URL%
    echo To view API docs, visit:        https://%ROUTE_URL%/docs
)
echo ================================================================================

endlocal