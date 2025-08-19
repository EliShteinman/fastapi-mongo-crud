#!/bin/bash
set -e

# ================================================================================
#  Deploys the FastAPI service using the advanced STATEFULSET approach.
# ================================================================================

# --- Step 0: Setup and Configuration ---
function print_header() {
  echo ""
  echo "================================================================================"
  echo "   $1"
  echo "================================================================================"
}

# Ensure script runs from the project root directory
cd "$(dirname "$0")"
PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"
echo "INFO: Running script from project root: $PROJECT_ROOT"

# Validate input parameter (Docker Hub username)
if [ -z "$1" ]; then
    echo "ERROR: Docker Hub username must be provided as the first argument."
    echo "Usage: ./scripts/deploy-statefulset.sh <your-dockerhub-username>"
    exit 1
fi
DOCKERHUB_USERNAME="$1"
IMAGE_NAME="fastapi-mongo-crud"

# Create a unique image tag (from git commit or timestamp)
IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || date +%s)
FULL_IMAGE_NAME="docker.io/${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
echo "INFO: Using image: ${FULL_IMAGE_NAME}"

# --- Step 1: Build and Push Docker Image ---
print_header "Step 1: Building and Pushing Docker Image"
docker buildx build --no-cache --platform linux/amd64,linux/arm64 -t "${FULL_IMAGE_NAME}" --push .
echo "SUCCESS: Image successfully pushed to Docker Hub."

# --- Step 2: Apply Infrastructure to OpenShift ---
print_header "Step 2: Applying Infrastructure to OpenShift"
echo "INFO: Using current OpenShift project: $(oc project -q)"
if ! oc project -q > /dev/null; then
    echo "ERROR: Failed to get current OpenShift project. Are you logged in?"
    exit 1
fi

K8S_DIR="infrastructure/k8s"

# Apply MongoDB manifests for StatefulSet
print_header "--> Deploying MongoDB (StatefulSet)..."
oc apply -f "$K8S_DIR/00-mongo-configmap.yaml"
oc apply -f "$K8S_DIR/01-mongo-secret.yaml"
# NOTE: A separate PVC is NOT applied. The StatefulSet manages it.
oc apply -f "$K8S_DIR/03a-mongo-statefulset.yaml"
oc apply -f "$K8S_DIR/04a-mongo-headless-service.yaml"

echo "INFO: Waiting for MongoDB pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
echo "SUCCESS: MongoDB pod is ready."

echo "INFO: Allowing time for MongoDB internal initialization..."
sleep 15
echo "SUCCESS: MongoDB is fully initialized."

# Apply FastAPI manifests for StatefulSet
print_header "--> Deploying FastAPI Application for StatefulSet..."
sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
    "$K8S_DIR/05a-fastapi-deployment-for-statefulset.yaml" | oc apply -f -
oc apply -f "$K8S_DIR/06a-fastapi-service-for-statefulset.yaml"

echo "INFO: Waiting for FastAPI pod to be ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api-stateful --timeout=300s
echo "SUCCESS: FastAPI Application is ready."

# Apply Route for StatefulSet
print_header "--> Exposing FastAPI with a Route for StatefulSet..."
oc apply -f "$K8S_DIR/07a-fastapi-route-for-statefulset.yaml"
echo "SUCCESS: Route created."

# Final step: Display the route
print_header "Deployment Complete!"
ROUTE_URL=$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')
if [ -z "$ROUTE_URL" ]; then
    echo "WARNING: Could not retrieve the application URL."
else
    echo "Your application is available at: https://${ROUTE_URL}"
    echo "To view API docs, visit:        https://${ROUTE_URL}/docs"
fi