# Deployment and Usage Guide: FastAPI and MongoDB Application for OpenShift

🌍 **Language:** **[English](demo_guide.md)** | [עברית](demo_guide.he.md)

This guide presents a complete deployment of application and infrastructure to OpenShift, step by step.
It covers two main deployment paths for the database:
1. **Deployment:** The standard and flexible way for deploying most applications.
2. **StatefulSet:** The recommended way for applications requiring stable network identity and persistent storage, like databases.

In each path, we'll demonstrate two deployment methods:
* **Declarative (with YAML files):** The recommended method for production (Infrastructure as Code).
* **Imperative (with direct CLI commands):** For quick use and development.

---

## Step 0: Preliminary Setup (Common to All Paths)

Ensure the following tools are installed and ready for use: `oc`, `docker`, `git`.

### 1. Connect to OpenShift
```bash
oc login --token=<your-token> --server=<your-server-url>
```

### 2. Create a New Project
```bash
oc new-project fastapi-mongo-demo
```

### 3. Login to Docker Hub
```bash
docker login
```

### 4. Set Variables
**!!! Important:** Execute this step in the terminal where you'll run the rest of the commands.

<details>
<summary>💻 <strong>For Linux / macOS</strong></summary>

```bash
# !!! Replace 'your-dockerhub-username' with your username !!!
export DOCKERHUB_USERNAME='your-dockerhub-username'
export IMAGE_TAG="demo-$(date +%s)"
export FULL_IMAGE_NAME="docker.io/${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG}"
```

</details>

<details>
<summary>🪟 <strong>For Windows (CMD)</strong></summary>

```batch
@REM !!! Replace 'your-dockerhub-username' with your username !!!
set "DOCKERHUB_USERNAME=your-dockerhub-username"
FOR /F "delims=" %%g IN ('powershell -NoProfile -Command "Get-Date -UFormat %s"') DO SET "IMAGE_TAG=demo-%%g"
set "FULL_IMAGE_NAME=docker.io/%DOCKERHUB_USERNAME%/fastapi-mongo-crud:%IMAGE_TAG%"
```
</details>

### 5. Build and Push Docker Image
The image will be shared across all deployment paths.

<details>
<summary>💻 <strong>For Linux / macOS</strong></summary>

```bash
echo "Building and pushing image: ${FULL_IMAGE_NAME}"
docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t "${FULL_IMAGE_NAME}" --push .
```

</details>

<details>
<summary>🪟 <strong>For Windows (CMD)</strong></summary>

```batch
echo "Building and pushing image: %FULL_IMAGE_NAME%"
docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t "%FULL_IMAGE_NAME%" --push .
```
</details>

---

## Path A: Deployment with `Deployment` (The Standard Approach)

### Part A - Declarative Deployment (YAML)
This is the recommended way for production.

#### 1. MongoDB Infrastructure Deployment

**Step 1.1: Create ConfigMap for Configuration Information**

The `00-mongo-configmap.yaml` file contains non-sensitive MongoDB configuration:
```bash
oc apply -f infrastructure/k8s/00-mongo-configmap.yaml
```
*What this does:* Creates a ConfigMap that stores root username, database name, and collection name.

**Step 1.2: Create Secret for Password**

The `01-mongo-secret.yaml` file contains encrypted sensitive information:
```bash
oc apply -f infrastructure/k8s/01-mongo-secret.yaml
```
*What this does:* Creates a Secret with MongoDB's encrypted root password.

**Step 1.3: Create PVC for Persistent Storage**

The `02-mongo-pvc.yaml` file requests persistent storage:
```bash
oc apply -f infrastructure/k8s/02-mongo-pvc.yaml
```
*What this does:* Creates a request for 2GB persistent storage so MongoDB data won't be lost during restarts.

**Step 1.4: Create MongoDB Deployment**

The `03-mongo-deployment.yaml` file defines how to run MongoDB:
```bash
oc apply -f infrastructure/k8s/03-mongo-deployment.yaml
```
*What this does:* Creates a Deployment that runs a MongoDB pod with all configurations, health check probes, and connection to persistent storage.

**Step 1.5: Create Database Service**

The `04-mongo-service.yaml` file exposes MongoDB within the cluster:
```bash
oc apply -f infrastructure/k8s/04-mongo-service.yaml
```
*What this does:* Creates a Service named `mongo-db-service` that allows other applications to connect to the database.

**Step 1.6: Wait for MongoDB Initialization**
```bash
echo "Waiting for MongoDB pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
echo "MongoDB pod is ready. Allowing time for internal initialization..."
sleep 15
echo "MongoDB is fully initialized!"
```

#### 2. FastAPI Application Deployment

**Step 2.1: Create FastAPI Deployment**

The `05-fastapi-deployment.yaml` file defines how to run our application:

<details>
<summary>💻 <strong>For Linux / macOS (with sed)</strong></summary>

```bash
sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
    "infrastructure/k8s/05-fastapi-deployment.yaml" | oc apply -f -
```
</details>

<details>
<summary>🪟 <strong>For Windows (with PowerShell)</strong></summary>

```batch
powershell -NoProfile -Command "(Get-Content -Raw infrastructure\k8s\05-fastapi-deployment.yaml) -replace 'docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest', '%FULL_IMAGE_NAME%' | oc apply -f -"
```
</details>

*What this does:* Creates a Deployment with the image we built, sets environment variables for database connection, and adds health check probes.

**Step 2.2: Create Application Service**

The `06-fastapi-service.yaml` file exposes the application within the cluster:
```bash
oc apply -f infrastructure/k8s/06-fastapi-service.yaml
```
*What this does:* Creates a Service named `mongo-api-service` that enables access to the application through port 8080.

**Step 2.3: Wait for Application Initialization**
```bash
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api --timeout=300s
echo "FastAPI is ready!"
```

#### 3. Expose Application to Internet

**Step 3.1: Create Route**

The `07-fastapi-route.yaml` file exposes the application to the internet:
```bash
oc apply -f infrastructure/k8s/07-fastapi-route.yaml
echo "Route created."
```
*What this does:* Creates a Route in OpenShift that gives us a public URL to access the application with HTTPS.

**Now, skip to the "API Usage and Testing" section.**

---

### Part B - Imperative Deployment (Direct Commands)
This method uses direct CLI commands instead of YAML files.
(Ensure there are no existing resources from the previous part).

#### 1. MongoDB Infrastructure Deployment

**Step 1.1: Create ConfigMap**
```bash
oc create configmap mongo-db-config \
  --from-literal=MONGO_INITDB_ROOT_USERNAME=mongoadmin \
  --from-literal=MONGO_DB_NAME=enemy_soldiers \
  --from-literal=MONGO_COLLECTION_NAME=soldier_details
```
*What this does:* Creates a ConfigMap with MongoDB configuration settings.

**Step 1.2: Create Secret**
```bash
oc create secret generic mongo-db-credentials \
  --from-literal=MONGO_INITDB_ROOT_PASSWORD='yourSuperSecretPassword123'
```
*What this does:* Creates a Secret with MongoDB's root password.

**Step 1.3: Create PVC (using YAML file)**
```bash
oc apply -f infrastructure/k8s/02-mongo-pvc.yaml
```
*What this does:* There's no simple way to create PVC imperatively, so we use the file.

**Step 1.4: Create MongoDB Deployment**
```bash
# Create the basic Deployment
oc create deployment mongo-db-deployment --image=mongo:8.0

# Add port to container (needed to expose it later)
oc patch deployment mongo-db-deployment -p '{"spec":{"template":{"spec":{"containers":[{"name":"mongo","ports":[{"containerPort":27017}]}]}}}}'

# Connect persistent storage
oc set volume deployment/mongo-db-deployment \
  --add --name=mongo-persistent-storage \
  --type=pvc --claim-name=mongo-db-pvc \
  --mount-path=/data/db

# Add environment variables from ConfigMap and Secret
oc set env deployment/mongo-db-deployment --from=configmap/mongo-db-config
oc set env deployment/mongo-db-deployment --from=secret/mongo-db-credentials

# Add labels for management
oc label deployment mongo-db-deployment \
  app.kubernetes.io/instance=mongo-db \
  app.kubernetes.io/name=mongo \
  app.kubernetes.io/part-of=mongo-loader-app
```

**Step 1.5: Create Service**
```bash
# Expose the Deployment as a Service
oc expose deployment mongo-db-deployment --port=27017 --name=mongo-db-service

# Add labels to Service
oc label service mongo-db-service \
  app.kubernetes.io/instance=mongo-db \
  app.kubernetes.io/name=mongo \
  app.kubernetes.io/part-of=mongo-loader-app
```

**Step 1.6: Wait for Initialization**
```bash
echo "Waiting for MongoDB pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
echo "MongoDB pod is ready. Allowing time for internal initialization..."
sleep 15
echo "MongoDB is fully initialized!"
```

#### 2. FastAPI Application Deployment

**Step 2.1: Create FastAPI Deployment**

<details>
<summary>💻 <strong>For Linux / macOS</strong></summary>

```bash
# Create the Deployment with our image
oc create deployment mongo-api-deployment --image="${FULL_IMAGE_NAME}"

# Add environment variables
oc set env deployment/mongo-api-deployment \
  MONGO_HOST=mongo-db-service \
  MONGO_PORT=27017
oc set env deployment/mongo-api-deployment --from=configmap/mongo-db-config
oc set env deployment/mongo-api-deployment --from=secret/mongo-db-credentials

# Add labels
oc label deployment mongo-api-deployment \
  app.kubernetes.io/instance=mongo-api \
  app.kubernetes.io/name=fastapi-mongo \
  app.kubernetes.io/part-of=mongo-loader-app
```

</details>

<details>
<summary>🪟 <strong>For Windows (CMD)</strong></summary>

```batch
@REM Create the Deployment with our image
oc create deployment mongo-api-deployment --image="%FULL_IMAGE_NAME%"

@REM Add environment variables
oc set env deployment/mongo-api-deployment MONGO_HOST=mongo-db-service MONGO_PORT=27017
oc set env deployment/mongo-api-deployment --from=configmap/mongo-db-config
oc set env deployment/mongo-api-deployment --from=secret/mongo-db-credentials

@REM Add labels
oc label deployment mongo-api-deployment app.kubernetes.io/instance=mongo-api app.kubernetes.io/name=fastapi-mongo app.kubernetes.io/part-of=mongo-loader-app
```
</details>

**Step 2.2: Create Application Service**
```bash
# Expose the application as a Service
oc expose deployment mongo-api-deployment --port=8080 --name=mongo-api-service

# Add labels to Service
oc label service mongo-api-service \
  app.kubernetes.io/instance=mongo-api \
  app.kubernetes.io/name=fastapi-mongo \
  app.kubernetes.io/part-of=mongo-loader-app
```

**Step 2.3: Wait for Initialization**
```bash
echo "Waiting for FastAPI pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api --timeout=300s
echo "FastAPI is ready!"
```

#### 3. Expose Application to Internet
```bash
# Create Route for external access
oc expose service mongo-api-service --name=mongo-api-route

# Add labels to Route
oc label route mongo-api-route \
  app.kubernetes.io/instance=mongo-api \
  app.kubernetes.io/name=fastapi-mongo \
  app.kubernetes.io/part-of=mongo-loader-app

echo "Route created."
```
**Now, skip to the "API Usage and Testing" section.**

---

## Path B: Deployment with `StatefulSet` (The Advanced Approach)

### 1. MongoDB Infrastructure Deployment

**Step 1.1: Create ConfigMap and Secret**
```bash
oc apply -f infrastructure/k8s/00-mongo-configmap.yaml
oc apply -f infrastructure/k8s/01-mongo-secret.yaml
```
*What this does:* Same as the previous path - creates configuration and password.

**Step 1.2: Create StatefulSet**

The `03a-mongo-statefulset.yaml` file creates a StatefulSet instead of Deployment:
```bash
oc apply -f infrastructure/k8s/03a-mongo-statefulset.yaml
```
*What this does:* Creates a StatefulSet that manages persistent storage automatically and gives each Pod a stable identity.

**Step 1.3: Create Headless Service**

The `04a-mongo-headless-service.yaml` file creates a special Service for StatefulSet:
```bash
oc apply -f infrastructure/k8s/04a-mongo-headless-service.yaml
```
*What this does:* Creates a Headless Service (without ClusterIP) that gives each Pod in the StatefulSet a unique and stable network address.

**Step 1.4: Wait for Initialization**
```bash
echo "Waiting for MongoDB StatefulSet pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
echo "MongoDB pod is ready. Allowing time for internal initialization..."
sleep 15
echo "MongoDB is fully initialized!"
```

### 2. FastAPI Application Deployment

**Step 2.1: Create FastAPI Deployment (Adapted for StatefulSet)**

The `05a-fastapi-deployment-for-statefulset.yaml` file is adapted to connect to Headless Service:

<details>
<summary>💻 <strong>For Linux / macOS (with sed)</strong></summary>

```bash
sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
    "infrastructure/k8s/05a-fastapi-deployment-for-statefulset.yaml" | oc apply -f -
```
</details>

<details>
<summary>🪟 <strong>For Windows (with PowerShell)</strong></summary>

```batch
powershell -NoProfile -Command "(Get-Content -Raw infrastructure\k8s\05a-fastapi-deployment-for-statefulset.yaml) -replace 'docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest', '%FULL_IMAGE_NAME%' | oc apply -f -"
```
</details>

*What this does:* Creates an application Deployment that connects to `mongo-db-headless-service` instead of regular Service.

**Step 2.2: Create Application Service**

The `06a-fastapi-service-for-statefulset.yaml` file creates a Service with adapted names:
```bash
oc apply -f infrastructure/k8s/06a-fastapi-service-for-statefulset.yaml
```

**Step 2.3: Wait for Initialization**
```bash
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api-stateful --timeout=300s
echo "FastAPI is ready!"
```

### 3. Expose Application

**Step 3.1: Create Route Adapted for StatefulSet**

The `07a-fastapi-route-for-statefulset.yaml` file creates a Route with adapted name:
```bash
oc apply -f infrastructure/k8s/07a-fastapi-route-for-statefulset.yaml
echo "Route created."
```

---

## Step 3: API Usage and Testing

After deployment is complete, find the application's URL.

<details>
<summary>💻 <strong>For Linux / macOS</strong></summary>

```bash
# Choose the line appropriate for your deployment path:

# For Deployment path (regular or imperative):
export ROUTE_URL=$(oc get route mongo-api-route -o jsonpath='{.spec.host}')

# For StatefulSet path:
# export ROUTE_URL=$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')

echo "Application URL: https://${ROUTE_URL}"
echo "API Documentation: https://${ROUTE_URL}/docs"
```
</details>

<details>
<summary>🪟 <strong>For Windows (CMD)</strong></summary>

```batch
@REM Choose the line appropriate for your deployment path:

@REM For Deployment path (regular or imperative):
FOR /F "usebackq delims=" %%g IN (`oc get route mongo-api-route -o jsonpath={.spec.host}`) DO SET "ROUTE_URL=%%g"

@REM For StatefulSet path:
@REM FOR /F "usebackq delims=" %%g IN (`oc get route mongo-api-route-stateful -o jsonpath={.spec.host}`) DO SET "ROUTE_URL=%%g"

echo Application URL: https://%ROUTE_URL%
echo API Documentation: https://%ROUTE_URL%/docs
```
</details>

### Usage Examples with `curl`

<details>
<summary>💻 <strong>For Linux / macOS</strong></summary>

**1. Get all soldiers**
```bash
curl "https://${ROUTE_URL}/soldiersdb/" | jq
```

**2. Create a new soldier**
```bash
curl -X POST "https://${ROUTE_URL}/soldiersdb/" \
  -H "Content-Type: application/json" \
  -d '{"ID": 101, "first_name": "John", "last_name": "Doe", "phone_number": 5551234, "rank": "Sergeant"}'
```

**3. Get specific soldier (ID=101)**
```bash
curl "https://${ROUTE_URL}/soldiersdb/101" | jq
```

**4. Update soldier (ID=101)**
```bash
curl -X PUT "https://${ROUTE_URL}/soldiersdb/101" \
  -H "Content-Type: application/json" \
  -d '{"rank": "Captain", "phone_number": 5555678}'
```

**5. Delete soldier (ID=101)**
```bash
curl -X DELETE "https://${ROUTE_URL}/soldiersdb/101"
```

</details>

<details>
<summary>🪟 <strong>For Windows (CMD)</strong></summary>

**1. Get all soldiers**
```batch
curl "https://%ROUTE_URL%/soldiersdb/" | jq
```

**2. Create a new soldier**
```batch
curl -X POST "https://%ROUTE_URL%/soldiersdb/" ^
  -H "Content-Type: application/json" ^
  -d "{\"ID\": 101, \"first_name\": \"John\", \"last_name\": \"Doe\", \"phone_number\": 5551234, \"rank\": \"Sergeant\"}"
```

**3. Get specific soldier (ID=101)**
```batch
curl "https://%ROUTE_URL%/soldiersdb/101" | jq
```

**4. Update soldier (ID=101)**
```batch
curl -X PUT "https://%ROUTE_URL%/soldiersdb/101" ^
  -H "Content-Type: application/json" ^
  -d "{\"rank\": \"Captain\", \"phone_number\": 5555678}"
```

**5. Delete soldier (ID=101)**
```batch
curl -X DELETE "https://%ROUTE_URL%/soldiersdb/101"
```

</details>

---

## Step 4: Environment Cleanup

### Option A: Selective deletion using labels
```bash
# Delete all components belonging to the application
oc delete all,pvc,secret,configmap -l app.kubernetes.io/part-of=mongo-loader-app
```

### Option B: Delete entire project
```bash
oc delete project fastapi-mongo-demo
```

---

## Tips and Troubleshooting

### Check component status
```bash
# Check all pods
oc get pods

# Check MongoDB logs
oc logs -l app.kubernetes.io/instance=mongo-db

# Check FastAPI logs
oc logs -l app.kubernetes.io/instance=mongo-api

# Check Routes
oc get routes
```

### Common issues
1. **Pod won't start:** Check logs with `oc logs <pod-name>`
2. **Can't reach application:** Ensure Route was created successfully
3. **Database connection issues:** Ensure MongoDB Service is running
4. **Storage issues:** Check that PVC was created and connected