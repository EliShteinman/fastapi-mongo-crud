#!/bin/bash
# This script automates the deployment process for the FastAPI MongoDB service
# using the advanced StatefulSet approach for the database.

# --- Technical Step: Ensure script runs from project root ---
cd "$(dirname "$0")/.." # Move to project root

# --- Configuration ---
if [ -z "$1" ]; then
    echo "ERROR: Docker Hub username must be provided as the first argument."
    echo "Usage: ./scripts/deploy-statefulset.sh <your-dockerhub-username>"
    exit 1
fi
DOCKERHUB_USERNAME="$1"
IMAGE_NAME="fastapi-mongo-crud"
IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || date +%s)
FULL_IMAGE_NAME="docker.io/${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"

set -e

function print_header() {
  echo ""
  echo "================================================================================"
  echo "   $1"
  echo "================================================================================"
}

# --- Main Script ---

# Step 1: Build and Push Docker Image
print_header "Step 1: Building and Pushing Docker Image"
echo "Image to be built: ${FULL_IMAGE_NAME}"
docker buildx build --no-cache --platform linux/amd64,linux/arm64 -t "${FULL_IMAGE_NAME}" --push .
echo "Image successfully pushed to Docker Hub."

# Step 2: Apply StatefulSet Infrastructure to OpenShift
print_header "Step 2: Applying StatefulSet Infrastructure to OpenShift"
echo "INFO: Using current OpenShift project: $(oc project -q)"

K8S_DIR="infrastructure/k8s"

# Apply MongoDB manifests for StatefulSet
print_header "--> Deploying MongoDB with StatefulSet..."
oc apply -f "$K8S_DIR/00-mongo-configmap.yaml"
oc apply -f "$K8S_DIR/01-mongo-secret.yaml"
oc apply -f "$K8S_DIR/03a-mongo-statefulset.yaml"
oc apply -f "$K8S_DIR/04a-mongo-headless-service.yaml"
echo "Waiting for MongoDB StatefulSet to be ready..."
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
echo "Waiting for FastAPI to be ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api-stateful --timeout=300s
echo "SUCCESS: FastAPI Application is ready."

# Apply Route for StatefulSet
print_header "--> Exposing FastAPI with a Route for StatefulSet..."
oc apply -f "$K8S_DIR/07a-fastapi-route-for-statefulset.yaml"
echo "SUCCESS: Route created."

# Final step: Display the route
print_header "Deployment Complete!"
ROUTE_URL=$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')
echo "Your application is available at the following URL:"
echo "https://${ROUTE_URL}"
echo ""
echo "To view the interactive API documentation (Swagger UI), navigate to:"
echo "https://${ROUTE_URL}/docs"