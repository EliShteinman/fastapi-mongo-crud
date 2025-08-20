# Kubernetes/OpenShift Manifests Documentation

🌍 **Language:** **[English](README.md)** | [עברית](README.he.md)

This guide explains the role of each YAML file in this directory, how they work together, and what each important part does.

## Overview

The application consists of two main components:
1. **MongoDB** - The database
2. **FastAPI** - The API that connects to the database

We have **two deployment paths**:
- **Deployment** - The standard way (regular files)
- **StatefulSet** - The recommended way for databases (files with 'a')

---

## Shared Components (for both paths)

### `00-mongo-configmap.yaml` - Non-sensitive configuration
```yaml
data:
  MONGO_INITDB_ROOT_USERNAME: "mongoadmin"    # Root username
  MONGO_DB_NAME: "enemy_soldiers"             # Database name (per requirements!)
  MONGO_COLLECTION_NAME: "soldier_details"   # Collection name (per requirements!)
```
**Why ConfigMap?** Non-sensitive information that can be viewed, easy to change without rebuilding the image.

### `01-mongo-secret.yaml` - Encrypted passwords
```yaml
data:
  MONGO_INITDB_ROOT_PASSWORD: amhzZHl0dGZlNjVmZHM1NHNjZjY1  # base64 encrypted
```
**Why Secret?** Passwords must be encrypted. OpenShift encrypts them automatically.

---

## Path 1: Deployment with Deployment (regular files)

### `02-mongo-pvc.yaml` - Storage request
```yaml
spec:
  accessModes:
    - ReadWriteOnce    # Only one pod can write
  resources:
    requests:
      storage: 2Gi     # Requests 2GB persistent storage
```
**Why PVC?** Without this, all MongoDB data would be lost when the pod is killed.

### `03-mongo-deployment.yaml` - Running MongoDB
**Important parts:**
```yaml
# Which image to use
image: docker.io/library/mongo:8.0

# How to get the configuration
envFrom:
  - configMapRef:
      name: mongo-db-config     # All variables from ConfigMap
  - secretRef:
      name: mongo-db-credentials # All variables from Secret

# Health checks - what's the difference between the two?
readinessProbe:                # "Is it ready to receive traffic?"
  exec:
    command: ["mongosh", "--eval", "db.adminCommand('ping')"]
  initialDelaySeconds: 10      # Wait 10 seconds after pod starts
  periodSeconds: 10           # Check every 10 seconds
  timeoutSeconds: 5           # If no response within 5 seconds - fail
  failureThreshold: 3         # After 3 failures - stop sending traffic (don't kill!)

livenessProbe:                 # "Is it still alive?"
  exec:
    command: ["mongosh", "--eval", "db.adminCommand('ping')"]
  initialDelaySeconds: 30      # Wait 30 seconds (more!) - give time to start
  periodSeconds: 15           # Check every 15 seconds (less frequent)
  timeoutSeconds: 5           # Response timeout
  failureThreshold: 3         # After 3 failures - kill pod and create new one!

# Resource management - how much CPU and memory needed
resources:
  requests:                   # "Guaranteed minimum" - OpenShift guarantees availability
    cpu: "200m"              # 200 milli-cores = 0.2 CPU core
    memory: "256Mi"          # 256 megabytes RAM
  limits:                     # "Maximum allowed" - cannot exceed
    cpu: "500m"              # 0.5 CPU core maximum - if exceeded, OpenShift throttles
    memory: "512Mi"          # 512 megabytes RAM maximum - if exceeded, OpenShift kills!

# Connection to persistent storage
volumeMounts:
  - name: mongo-persistent-storage
    mountPath: /data/db        # Where MongoDB stores data
volumes:
  - name: mongo-persistent-storage
    persistentVolumeClaim:
      claimName: mongo-db-pvc  # Connect to PVC we created
```

### `04-mongo-service.yaml` - Internal address for MongoDB
```yaml
spec:
  selector:
    app.kubernetes.io/instance: mongo-db  # Connect to all pods with this label
  ports:
    - port: 27017              # Standard MongoDB port
      targetPort: 27017
```
**What does this do?** Creates address `mongo-db-service:27017` that the API can use.

### `05-fastapi-deployment.yaml` - Running the API
**Important parts:**
```yaml
# Which image to use (this is replaced in deployment script)
image: "docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest"

# Environment variables the API needs
env:
  - name: MONGO_HOST
    value: "mongo-db-service"    # MongoDB Service name
  - name: MONGO_PORT
    value: "27017"
  - name: MONGO_USER
    valueFrom:
      configMapKeyRef:           # Take from ConfigMap
        name: mongo-db-config
        key: MONGO_INITDB_ROOT_USERNAME
  - name: MONGO_PASSWORD
    valueFrom:
      secretKeyRef:              # Take from Secret (encrypted!)
        name: mongo-db-credentials
        key: MONGO_INITDB_ROOT_PASSWORD

# API health checks - two different endpoints!
readinessProbe:               # "Is it ready to work?"
  httpGet:
    path: /health             # Also checks database connection - if MongoDB disconnected, fails!
    port: 8080
  initialDelaySeconds: 15     # Wait 15 seconds after pod starts
  periodSeconds: 10          # Check every 10 seconds

livenessProbe:               # "Is it still alive?"
  httpGet:
    path: /                  # Only checks if server responds - doesn't check database
    port: 8080
  initialDelaySeconds: 20     # Wait 20 seconds (more than readiness!)
  periodSeconds: 20          # Check every 20 seconds (less frequent)

# Resource management - API needs less than MongoDB
resources:
  requests:                  # Guaranteed minimum
    cpu: "50m"              # 0.05 CPU core - light Python application
    memory: "128Mi"         # 128 megabytes RAM
  limits:                    # Maximum allowed
    cpu: "200m"             # 0.2 CPU core maximum
    memory: "256Mi"         # 256 megabytes RAM maximum
```

### `06-fastapi-service.yaml` - Internal address for API
```yaml
spec:
  selector:
    app.kubernetes.io/instance: mongo-api  # Connect to API pods
  ports:
    - port: 8080
      targetPort: 8080
```

### `07-fastapi-route.yaml` - Public address
```yaml
spec:
  to:
    kind: Service
    name: mongo-api-service    # Point to API Service
  tls:
    termination: edge          # Automatic HTTPS
    insecureEdgeTerminationPolicy: Redirect  # Redirect HTTP to HTTPS
```
**What does this do?** Creates public URL like `https://mongo-api-route-xxx.apps.cluster.com`

---

## Path 2: Deployment with StatefulSet (files with 'a')

### Why is StatefulSet better for databases?
1. **Stable identity** - Each pod gets a fixed name (mongo-db-statefulset-0)
2. **Ordered deployment** - Pods start and stop in defined order
3. **Automatic storage** - Creates PVC automatically for each pod

### `03a-mongo-statefulset.yaml` - StatefulSet instead of Deployment
**Main differences:**
```yaml
kind: StatefulSet              # Instead of Deployment
spec:
  serviceName: "mongo-db-headless-service"  # Needs Headless Service

# Instead of regular volumes:
volumeClaimTemplates:          # Creates PVC automatically!
- metadata:
    name: mongo-persistent-storage
  spec:
    accessModes: [ "ReadWriteOnce" ]
    resources:
      requests:
        storage: 2Gi
```

### `04a-mongo-headless-service.yaml` - Special Service for StatefulSet
```yaml
spec:
  clusterIP: None              # This is what makes it "headless"
```
**Why headless?** StatefulSet needs this to give each pod a unique address.

### Adapted API files (05a, 06a, 07a)
The only difference:
```yaml
# In regular files:
name: mongo-api
value: "mongo-db-service"

# In StatefulSet files:
name: mongo-api-stateful
value: "mongo-db-headless-service"
```

---

## How to choose between paths?

### Use Deployment if:
- You're starting out and want something simple
- You don't mind losing data (for development)
- You only have one MongoDB

### Use StatefulSet if:
- You want a stable database (production)
- Data persistence is important to you
- You plan to scale to MongoDB replica set in the future

---

## Correct deployment order

### Deployment:
```bash
oc apply -f 00-mongo-configmap.yaml
oc apply -f 01-mongo-secret.yaml
oc apply -f 02-mongo-pvc.yaml
oc apply -f 03-mongo-deployment.yaml
oc apply -f 04-mongo-service.yaml
# Wait for MongoDB to be ready
oc apply -f 05-fastapi-deployment.yaml
oc apply -f 06-fastapi-service.yaml
oc apply -f 07-fastapi-route.yaml
```

### StatefulSet:
```bash
oc apply -f 00-mongo-configmap.yaml
oc apply -f 01-mongo-secret.yaml
oc apply -f 03a-mongo-statefulset.yaml
oc apply -f 04a-mongo-headless-service.yaml
# Wait for MongoDB to be ready
oc apply -f 05a-fastapi-deployment-for-statefulset.yaml
oc apply -f 06a-fastapi-service-for-statefulset.yaml
oc apply -f 07a-fastapi-route-for-statefulset.yaml
```

---

## Health verification

### Check everything is working:
```bash
# Check all pods are running
oc get pods

# Check services are available
oc get svc

# Get public URL
oc get route

# Check API is working
curl https://your-route-url/health
```

### Common troubleshooting:
```bash
# If pod won't start
oc describe pod <pod-name>
oc logs <pod-name>

# If no database connection
oc exec -it <mongo-pod> -- mongosh
```