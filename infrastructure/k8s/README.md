# Kubernetes/OpenShift Manifests Documentation

🌍 **Language:** **[English](README.md)** | [עברית](README.he.md)

This guide explains the role of each YAML file in this directory, how they work together, and what each important part does. The guide focuses on deep understanding of each component and why it's built this way.

## Overview

The application consists of two main components:
1. **MongoDB** - The database
2. **FastAPI** - The API that connects to the database

We have **two deployment paths** with significant differences:

### Path A: Deployment (regular files)
- **Suitable for development and testing**
- Separate PVC created in advance
- Simpler to understand
- MongoDB can "move" between nodes

### Path B: StatefulSet (files with 'a')
- **Suitable for production**
- Automatic storage management
- Stable network identity for each Pod
- Guaranteed deployment order

---

## Shared Components (for both paths)

### `00-mongo-configmap.yaml` - Non-sensitive configuration

```yaml
data:
  MONGO_INITDB_ROOT_USERNAME: "mongoadmin"    # Root username
  MONGO_DB_NAME: "enemy_soldiers"             # Database name (per requirements!)
  MONGO_COLLECTION_NAME: "soldier_details"   # Collection name (per requirements!)
```

**Why ConfigMap and not Secrets?**
- ConfigMap for data that can be viewed (names, settings)
- Easy to change without rebuilding the image
- Accessible for reading and editing

**Why "enemy_soldiers"?**
This is the database name according to the project's technical requirements.

### `01-mongo-secret.yaml` - Encrypted passwords

```yaml
data:
  MONGO_INITDB_ROOT_PASSWORD: amhzZHl0dGZlNjVmZHM1NHNjZjY1  # base64 encrypted
```

**Why Secret and not ConfigMap?**
- Passwords must be encrypted
- OpenShift encrypts them automatically in the internal database
- Don't appear in logs or printouts

**How to decode the password?**
```bash
echo "amhzZHl0dGZlNjVmZHM1NHNjZjY1" | base64 -d
# Output: jhsdyttfe65fds54scf65
```

---

## Path A: Deployment with Deployment (Standard Approach)

### `02-mongo-pvc.yaml` - Persistent storage request

```yaml
spec:
  accessModes:
    - ReadWriteOnce    # ★ Only one pod can write simultaneously ★
  resources:
    requests:
      storage: 2Gi     # Requests 2GB persistent storage
```

**Why is PVC needed?**
Without this, all MongoDB data would be lost when the pod is killed or updated. It's like running a database on RAM memory - everything gets deleted on shutdown.

**What is ReadWriteOnce?**
- **ReadWriteOnce (RWO)**: Only one pod can write
- **ReadWriteMany (RWX)**: Multiple pods can write (not supported by all clouds)
- **ReadOnlyMany (ROX)**: Multiple pods can read

### `03-mongo-deployment.yaml` - Running MongoDB

This is the most complex file, let's break it down:

#### Image Selection
```yaml
image: docker.io/library/mongo:8.0
```
**Why Mongo 8.0?** Stable version with long-term support, compatible with Python's AsyncMongoClient.

#### Configuration Management
```yaml
envFrom:
  - configMapRef:
      name: mongo-db-config     # All variables from ConfigMap
  - secretRef:
      name: mongo-db-credentials # All variables from Secret
```

**Why `envFrom` instead of `env`?**
Instead of defining each variable separately, we "pour" all contents of ConfigMap and Secret as environment variables.

#### Health Checks - The Critical Difference

```yaml
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
```

**What's the difference?**
- **readinessProbe**: Decides whether to send traffic to pod
- **livenessProbe**: Decides whether to kill the pod and restart

**Why different timings?**
- readiness faster - want to know quickly that service is available
- liveness slower - don't want to kill pod due to temporary delay

#### Resource Management - The Heart of Performance

```yaml
resources:
  requests:                   # ★ "Guaranteed minimum" ★
    cpu: "200m"              # 200 milli-cores = 0.2 CPU core
    memory: "256Mi"          # 256 megabytes RAM
  limits:                     # ★ "Maximum allowed" ★
    cpu: "500m"              # 0.5 CPU core maximum
    memory: "512Mi"          # 512 megabytes RAM maximum
```

**Why this is critical?**
- **requests**: Kubernetes guarantees these resources will be available
- **limits**: Kubernetes doesn't let container exceed this

**What happens if exceeded?**
- **CPU limit**: Container is throttled (slowed down)
- **Memory limit**: Container is killed (OOMKilled)

**How to choose values?**
1. Start with a guess
2. Monitor usage with `kubectl top pods`
3. Adjust as needed

#### Connection to Persistent Storage

```yaml
volumeMounts:
  - name: mongo-persistent-storage
    mountPath: /data/db        # ★ Where MongoDB stores data ★
volumes:
  - name: mongo-persistent-storage
    persistentVolumeClaim:
      claimName: mongo-db-pvc  # Connect to PVC we created
```

**Why `/data/db`?** This is the standard path where MongoDB stores all its data.

### `04-mongo-service.yaml` - Internal address for MongoDB

```yaml
spec:
  selector:
    app.kubernetes.io/instance: mongo-db  # ★ How Service finds pods ★
  ports:
    - port: 27017              # Standard MongoDB port
      targetPort: 27017
```

**What does this do?**
Creates internal DNS address `mongo-db-service:27017` that the API can use. It's like an internal phonebook of the cluster.

**Why not direct IP?**
Because pod IPs change all the time. The Service provides a stable address.

### `05-fastapi-deployment.yaml` - Running the API

#### Sophisticated Environment Variables

```yaml
env:
  - name: MONGO_HOST
    value: "mongo-db-service"    # ★ MongoDB Service name ★
  - name: MONGO_PORT
    value: "27017"
  - name: MONGO_USER
    valueFrom:
      configMapKeyRef:           # ★ Take from ConfigMap ★
        name: mongo-db-config
        key: MONGO_INITDB_ROOT_USERNAME
  - name: MONGO_PASSWORD
    valueFrom:
      secretKeyRef:              # ★ Take from Secret (encrypted!) ★
        name: mongo-db-credentials
        key: MONGO_INITDB_ROOT_PASSWORD
```

**Why `valueFrom` instead of `value`?**
This allows direct linking to ConfigMap and Secret. If we change the value in ConfigMap, the new pod will get the new value automatically.

#### API Health Checks - Two different endpoints!

```yaml
readinessProbe:               # "Is it ready to work?"
  httpGet:
    path: /health             # ★ Also checks database connection! ★
    port: 8080
  initialDelaySeconds: 15     # Wait 15 seconds after pod starts
  periodSeconds: 10          # Check every 10 seconds

livenessProbe:               # "Is it still alive?"
  httpGet:
    path: /                  # ★ Only checks if server responds ★
    port: 8080
  initialDelaySeconds: 20     # Wait 20 seconds (more than readiness!)
  periodSeconds: 20          # Check every 20 seconds (less frequent)
```

**Why two different endpoints?**
- `/health`: Advanced endpoint that also checks database connection
- `/`: Basic endpoint that only checks if server is running

This prevents a situation where the API is "alive" but can't connect to the database.

#### Resource Management - API needs less

```yaml
resources:
  requests:                  # Guaranteed minimum
    cpu: "50m"              # 0.05 CPU core - light Python application
    memory: "128Mi"         # 128 megabytes RAM
  limits:                    # Maximum allowed
    cpu: "200m"             # 0.2 CPU core maximum
    memory: "256Mi"         # 256 megabytes RAM maximum
```

**Why less than MongoDB?**
API handling HTTP requests usually consumes fewer resources than database holding data in memory.

### `06-fastapi-service.yaml` and `07-fastapi-route.yaml`

**Service**: Creates internal address `mongo-api-service:8080`

**Route**: Creates public URL with automatic HTTPS:
```yaml
tls:
  termination: edge          # ★ Automatic HTTPS ★
  insecureEdgeTerminationPolicy: Redirect  # ★ Redirect HTTP to HTTPS ★
```

---

## Path B: Deployment with StatefulSet (Advanced Approach)

### Why is StatefulSet better for databases?

#### 1. Stable Identity
```bash
# Deployment
mongo-db-deployment-7d4f8b9c8-x7k2m  # Random name
mongo-db-deployment-7d4f8b9c8-p9q1n  # Random name

# StatefulSet  
mongo-db-statefulset-0                # Fixed name!
mongo-db-statefulset-1                # Fixed name!
```

#### 2. Guaranteed Deployment Order
- Pods start in order: 0, 1, 2...
- Pod 1 won't start until Pod 0 is ready
- Important for databases with clustering

#### 3. Automatic Storage for Each Pod
Each Pod gets its own PVC automatically - no need to create in advance.

### `03a-mongo-statefulset.yaml` - StatefulSet instead of Deployment

**Main differences:**

#### serviceName field
```yaml
kind: StatefulSet
spec:
  serviceName: "mongo-db-headless-service"  # ★ Needs Headless Service ★
```

#### volumeClaimTemplates - The Magic
```yaml
volumeClaimTemplates:          # ★ Creates PVC automatically! ★
- metadata:
    name: mongo-persistent-storage
  spec:
    accessModes: [ "ReadWriteOnce" ]
    resources:
      requests:
        storage: 2Gi
```

**What does this do?**
Instead of creating PVC in advance, StatefulSet creates new PVC for each Pod:
- `mongo-persistent-storage-mongo-db-statefulset-0`
- `mongo-persistent-storage-mongo-db-statefulset-1`

### `04a-mongo-headless-service.yaml` - Special Service for StatefulSet

```yaml
spec:
  clusterIP: None              # ★ This is what makes it "headless" ★
```

**What is Headless Service?**
- Regular Service: Has one IP that routes to all pods
- Headless Service: Has no IP, but gives unique DNS to each pod

**Why does StatefulSet need this?**
This gives each Pod a unique DNS address:
- `mongo-db-statefulset-0.mongo-db-headless-service`
- `mongo-db-statefulset-1.mongo-db-headless-service`

Important for databases with clustering that need to know how to reach specific pod.

### Adapted API files (05a, 06a, 07a)

The only difference:
```yaml
# In regular files:
MONGO_HOST: "mongo-db-service"

# In StatefulSet files:
MONGO_HOST: "mongo-db-headless-service"
```

---

## Detailed Comparison: Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| **Pod Name** | Random (hash) | Fixed and ordered |
| **Deployment Order** | All pods together | In order, one after another |
| **Storage** | Separate PVC, manual | Automatic PVC per pod |
| **DNS** | Regular Service | Headless Service + unique DNS |
| **Suitable for** | Stateless applications | Databases, clustering |
| **Complexity** | Simple | More sophisticated |
| **Recovery Time** | Fast | Slower (due to order) |

## Deployment Order Examples

### Deployment
```bash
# All pods start at once
kubectl apply -f 03-mongo-deployment.yaml

Pod mongo-db-deployment-xxx-abc  Creating...
Pod mongo-db-deployment-xxx-def  Creating...
Pod mongo-db-deployment-xxx-ghi  Creating...
# All start in parallel
```

### StatefulSet
```bash
# Pods start in order
kubectl apply -f 03a-mongo-statefulset.yaml

Pod mongo-db-statefulset-0  Creating...
Pod mongo-db-statefulset-0  Ready ✓
Pod mongo-db-statefulset-1  Creating...  # Only after 0 is ready
Pod mongo-db-statefulset-1  Ready ✓
Pod mongo-db-statefulset-2  Creating...  # Only after 1 is ready
```

---

## How to Choose Between Paths?

### Use Deployment if:
- You're starting and want something simple
- It's development/testing environment
- You don't mind losing data
- You have only one MongoDB
- You want fast deployment

### Use StatefulSet if:
- It's production environment
- Data persistence is important to you
- You plan to scale to MongoDB replica set in future
- You need stable identity for pods
- You're ready to deal with additional complexity

---

## Correct Deployment Order

### Deployment:
```bash
# 1. Basic settings
oc apply -f 00-mongo-configmap.yaml
oc apply -f 01-mongo-secret.yaml

# 2. Storage and MongoDB
oc apply -f 02-mongo-pvc.yaml      # ★ PVC before pod! ★
oc apply -f 03-mongo-deployment.yaml
oc apply -f 04-mongo-service.yaml

# 3. Wait for MongoDB to be ready
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s

# 4. API
oc apply -f 05-fastapi-deployment.yaml
oc apply -f 06-fastapi-service.yaml
oc apply -f 07-fastapi-route.yaml
```

### StatefulSet:
```bash
# 1. Basic settings
oc apply -f 00-mongo-configmap.yaml
oc apply -f 01-mongo-secret.yaml

# 2. StatefulSet and Headless Service
oc apply -f 03a-mongo-statefulset.yaml     # ★ Automatic storage! ★
oc apply -f 04a-mongo-headless-service.yaml

# 3. Wait for MongoDB to be ready
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s

# 4. Adapted API
oc apply -f 05a-fastapi-deployment-for-statefulset.yaml
oc apply -f 06a-fastapi-service-for-statefulset.yaml
oc apply -f 07a-fastapi-route-for-statefulset.yaml
```

---

## Health Verification and Troubleshooting

### Basic Check Commands

```bash
# Check all pods are running
oc get pods -l app.kubernetes.io/part-of=mongo-loader-app

# Check services are available
oc get svc -l app.kubernetes.io/part-of=mongo-loader-app

# Get public URL
oc get route
```

### Common Troubleshooting

#### Pod won't start
```bash
# 1. Check status
oc describe pod <pod-name>

# 2. Check logs
oc logs <pod-name>

# 3. Check events
oc get events --sort-by=.metadata.creationTimestamp
```

**Common issues:**
- `ImagePullBackOff`: Problem downloading image
- `CrashLoopBackOff`: Pod crashes immediately after starting
- `Pending`: No free resources or PVC problem

#### No database connection
```bash
# 1. Check MongoDB is running
oc exec -it <mongo-pod> -- mongosh

# 2. Check Service
oc describe svc mongo-db-service

# 3. Check connectivity
oc exec -it <api-pod> -- nslookup mongo-db-service
```

#### Storage issues
```bash
# Check PVC status
oc get pvc

# Check if bound to PV
oc describe pvc mongo-db-pvc

# Check storage class
oc get storageclass
```

**PVC Statuses:**
- `Pending`: Waiting for available PV
- `Bound`: Successfully connected to PV
- `Lost`: PV was lost

---

## Advanced Tips

### 1. How to check resource usage
```bash
# Current usage
oc top pods

# History (if monitoring available)
oc describe pod <pod-name> | grep -A 5 "Resource Usage"
```

### 2. How to resize storage
For StatefulSet:
```bash
# Edit the template
oc edit statefulset mongo-db-statefulset

# Change storage in volumeClaimTemplates
storage: 5Gi  # instead of 2Gi
```

### 3. How to migrate from Deployment to StatefulSet
```bash
# 1. Backup data
oc exec -it <mongo-pod> -- mongodump --archive > backup.archive

# 2. Delete Deployment
oc delete -f 03-mongo-deployment.yaml
oc delete -f 02-mongo-pvc.yaml

# 3. Deploy StatefulSet
oc apply -f 03a-mongo-statefulset.yaml

# 4. Restore data
oc exec -i <new-mongo-pod> -- mongorestore --archive < backup.archive
```

### 4. Monitoring and alerting
Add to pods:
```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/health"
```

This will allow Prometheus to collect metrics from the application.