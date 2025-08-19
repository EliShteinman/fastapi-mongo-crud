@echo off
setlocal

REM This script automates the entire deployment process for the FastAPI MongoDB service
REM using the standard Deployment approach.

REM === Technical Step: Ensure script runs from project root ===
cd /d "%~dp0\.."

REM --- Configuration ---
IF "%~1"=="" (
    echo [ERROR] Docker Hub username must be provided as the first argument.
    echo [USAGE] .\scripts\deploy.bat ^<your-dockerhub-username^>
    exit /b 1
)
SET "DOCKERHUB_USERNAME=%~1"
SET "IMAGE_NAME=fastapi-mongo-crud"

REM --- Create a unique tag from git hash or a timestamp ---
FOR /F "tokens=*" %%g IN ('git rev-parse --short HEAD 2^>nul') DO SET "IMAGE_TAG=%%g"
IF NOT DEFINED IMAGE_TAG (
    FOR /F "tokens=*" %%g IN ('powershell -Command "Get-Date -UFormat +%%s"') DO SET "IMAGE_TAG=%%g"
)
SET "FULL_IMAGE_NAME=docker.io/%DOCKERHUB_USERNAME%/%IMAGE_NAME%:%IMAGE_TAG%"

REM --- Helper Function for Headers ---
echo.
echo ================================================================================
echo    Step 1: Building and Pushing Docker Image
echo ================================================================================
echo [INFO] Image to be built: %FULL_IMAGE_NAME%
docker buildx build --no-cache --platform linux/amd64,linux/arm64 -t "%FULL_IMAGE_NAME%" --push .
IF %ERRORLEVEL% NEQ 0 ( echo [ERROR] Docker build failed. & exit /b 1 )
echo [SUCCESS] Image successfully pushed to Docker Hub.

REM --- Step 2: Apply Infrastructure to OpenShift ---
echo.
echo ================================================================================
echo    Step 2: Applying Infrastructure to OpenShift
echo ================================================================================
echo [INFO] Using current OpenShift project:
oc project -q

SET "K8S_DIR=infrastructure\k8s"

echo.
echo ---^> Deploying MongoDB...
REM UPDATED: Added the new ConfigMap
oc apply -f %K8S_DIR%\00-mongo-configmap.yaml
oc apply -f %K8S_DIR%\01-mongo-secret.yaml
oc apply -f %K8S_DIR%\02-mongo-pvc.yaml
oc apply -f %K8S_DIR%\03-mongo-deployment.yaml
oc apply -f %K8S_DIR%\04-mongo-service.yaml
echo [INFO] Waiting for MongoDB pod to become ready...
REM UPDATED: Using the new standard label
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
IF %ERRORLEVEL% NEQ 0 ( echo [ERROR] MongoDB pod did not become ready. & exit /b 1 )
echo [SUCCESS] MongoDB pod is ready.

REM ADDED: Wait for MongoDB internal initialization
echo [INFO] Allowing time for MongoDB internal initialization...
timeout /t 15 >nul
echo [SUCCESS] MongoDB is fully initialized.

echo.
echo ---^> Deploying FastAPI Application...
powershell -Command "(Get-Content -Raw %K8S_DIR%\05-fastapi-deployment.yaml).Replace('docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest', '%FULL_IMAGE_NAME%') | oc apply -f -"
oc apply -f %K8S_DIR%\06-fastapi-service.yaml
echo [INFO] Waiting for FastAPI to be ready...
REM UPDATED: Using the new standard label
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api --timeout=300s
IF %ERRORLEVEL% NEQ 0 ( echo [ERROR] FastAPI pod did not become ready. & exit /b 1 )
echo [SUCCESS] FastAPI Application is ready.

echo.
echo ---^> Exposing FastAPI with a Route...
oc apply -f %K8S_DIR%\07-fastapi-route.yaml
echo [SUCCESS] Route created.

echo.
echo ================================================================================
echo    Deployment Complete!
echo ================================================================================
FOR /F "tokens=*" %%g IN ('oc get route mongo-api-route -o jsonpath="{.spec.host}"') DO SET "ROUTE_URL=%%g"
echo Your application is available at the following URL:
REM UPDATED: Displaying the URL with https
echo https://%ROUTE_URL%
echo.
echo To view the interactive API documentation (Swagger UI), navigate to:
echo https://%ROUTE_URL%/docs
echo ================================================================================

endlocal