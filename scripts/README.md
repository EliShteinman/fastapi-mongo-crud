# Scripts Directory - Deployment and Testing Scripts

🌍 **Language:** **[English](README.md)** | [עברית](README.he.md)

This directory contains all the tools needed for automated deployment and testing of the FastAPI MongoDB application. Each script is designed to operate independently and provides complete automation.

## Files in Directory

### 🚀 Automated Deployment Scripts
- **`deploy.sh` / `deploy.bat`** - Standard deployment (Deployment + PVC)
- **`deploy-statefulset.sh` / `deploy-statefulset.bat`** - Advanced deployment (StatefulSet)
- **`run_api_tests.sh`** - End-to-end API testing script

### 📚 Guides
- **`demo_guide.md`** - 📖 **Independent manual deployment guide** - Learn step-by-step deployment without scripts

---

## Two Deployment Approaches

### 🚀 **Method 1: Automated (Fast)**
Use the ready-made scripts:

```bash
# Linux/macOS - Standard approach
./scripts/deploy.sh your-dockerhub-username

# Linux/macOS - Advanced approach (recommended)
./scripts/deploy-statefulset.sh your-dockerhub-username

# Windows
.\scripts\deploy.bat your-dockerhub-username
.\scripts\deploy-statefulset.bat your-dockerhub-username
```

### 📚 **Method 2: Manual (Deep Learning)**
📖 **For complete manual deployment guide with explanation of each step:**
**[demo_guide.md](demo_guide.md)**

The guide teaches:
- Manual deployment of all components
- Understanding the manifests
- Detailed `oc` commands
- `curl` examples for API testing
- Troubleshooting

### 🧪 **API Testing**
After deployment (either method):
```bash
./scripts/run_api_tests.sh https://your-app-url
```

---

## Detailed Analysis of Scripts

### 🤖 Automated Deployment Scripts

#### Script 1: `deploy.sh/bat` - The Standard Approach

**What the script does:**

1. **Preliminary checks:**
   ```bash
   # Verify running from project directory
   PROJECT_ROOT=$(git rev-parse --show-toplevel)
   cd "$PROJECT_ROOT"
   
   # Parameter validation
   if [ -z "$1" ]; then
       echo "ERROR: Docker Hub username required"
       exit 1
   fi
   ```

2. **Create unique image tag:**
   ```bash
   # Use git commit or timestamp
   IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || date +%s)
   FULL_IMAGE_NAME="docker.io/${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG}"
   ```
   
   **Why unique tag?** Ensures each deployment uses a new image, prevents cache issues.

3. **Advanced build and push:**
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t "${FULL_IMAGE_NAME}" --push .
   ```
   
   **Why `buildx`?** Multi-platform support (Intel and ARM), important for cloud deployment.

4. **MongoDB deployment (Deployment):**
   ```bash
   oc apply -f infrastructure/k8s/00-mongo-configmap.yaml
   oc apply -f infrastructure/k8s/01-mongo-secret.yaml
   oc apply -f infrastructure/k8s/02-mongo-pvc.yaml        # ★ Separate PVC ★
   oc apply -f infrastructure/k8s/03-mongo-deployment.yaml
   oc apply -f infrastructure/k8s/04-mongo-service.yaml
   ```

5. **Smart wait for MongoDB:**
   ```bash
   oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
   sleep 15  # Additional time for internal initialization
   ```
   
   **Why two steps?** `wait` waits for pod to start, `sleep` gives time for MongoDB to be ready for connections.

6. **FastAPI deployment with image replacement:**
   ```bash
   sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
       "infrastructure/k8s/05-fastapi-deployment.yaml" | oc apply -f -
   ```
   
   **The sed trick:** Replaces placeholder with real image in real-time.

#### Script 2: `deploy-statefulset.sh/bat` - The Advanced Approach

**Main differences:**

1. **No separate PVC:**
   ```bash
   # No:
   # oc apply -f 02-mongo-pvc.yaml
   
   # Yes:
   oc apply -f infrastructure/k8s/03a-mongo-statefulset.yaml  # ★ Automatic storage ★
   ```

2. **Headless Service:**
   ```bash
   oc apply -f infrastructure/k8s/04a-mongo-headless-service.yaml
   ```

3. **API adapted for StatefulSet:**
   ```bash
   # Connects to headless service instead of regular service
   sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
       "infrastructure/k8s/05a-fastapi-deployment-for-statefulset.yaml" | oc apply -f -
   ```

**When to use each script?**

| Feature | deploy.sh | deploy-statefulset.sh |
|---------|-----------|---------------------|
| **Deployment Speed** | Fast | Slower |
| **Data Reliability** | Basic | High |
| **Complexity** | Simple | Sophisticated |
| **Suitable for** | Development/testing | Production |
| **Data Recovery** | Manual | Automatic |

### 🧪 Testing Script: `run_api_tests.sh`

This is the smartest script - it performs comprehensive API testing:

#### Test Phases:

**Phase 0: Preliminary Cleanup**
```bash
# Delete data from previous tests (if any)
curl -s -o /dev/null -X DELETE "${FULL_URL}/${SOLDIER_1_ID}"
curl -s -o /dev/null -X DELETE "${FULL_URL}/${SOLDIER_2_ID}"
```

**Phase 1: Creation (CREATE)**
```bash
# Check database is empty
RESPONSE_BODY=$(curl -s -w "\n%{http_code}" "${FULL_URL}/")
STATUS_CODE=$(echo "$RESPONSE_BODY" | tail -n1)
BODY=$(echo "$RESPONSE_BODY" | sed '$d')

if [ "$STATUS_CODE" = "200" ] && [ "$(echo "$BODY" | jq 'length')" -eq 0 ]; then
    echo "✅ PASSED: Database is empty"
else
    echo "❌ FAILED: Database not empty"
    exit 1
fi
```

**The curl trick with -w:**
- `-w "\n%{http_code}"` adds status code at the end
- `tail -n1` takes the last line (status code)
- `sed '$d'` deletes the last line (returns the body)

**Phase 2: Error Testing**
```bash
# Try to create duplicate soldier (should fail)
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${FULL_URL}/" \
  -H "Content-Type: application/json" -d "$JSON_SOLDIER_1")
  
if [ "$STATUS_CODE" = "409" ]; then
    echo "✅ PASSED: Duplicate ID correctly rejected"
else
    echo "❌ FAILED: Expected 409, got $STATUS_CODE"
    exit 1
fi
```

**Phase 3: Full CRUD**
- UPDATE with partial data
- DELETE with verification that record was deleted
- Check 404 for non-existent records

**Phase 4: Final Cleanup**
```bash
# Verify database is back to empty
RESPONSE_BODY=$(curl -s -w "\n%{http_code}" "${FULL_URL}/")
STATUS_CODE=$(echo "$RESPONSE_BODY" | tail -n1)
BODY=$(echo "$RESPONSE_BODY" | sed '$d')

if [ "$STATUS_CODE" = "200" ] && [ "$(echo "$BODY" | jq 'length')" -eq 0 ]; then
    echo "✅ PASSED: Final cleanup successful"
else
    echo "❌ FAILED: Database not clean after tests"
fi
```

#### What the script tests:

✅ **Functionality:**
- Creating new soldiers
- Reading all soldiers
- Reading specific soldier
- Updating existing soldier
- Deleting soldier

✅ **Error handling:**
- 409 - Duplicate soldier
- 404 - Soldier not found
- 422 - Invalid data

✅ **Data consistency:**
- Data persists after creation
- Data changes after update
- Data disappears after delete

### 📚 Manual Guide: `demo_guide.md`

This is a **completely independent** guide that teaches how to deploy without scripts:

#### What the guide covers:

**Part 1: Basic Preparations**
- Connecting to OpenShift
- Building Docker image
- Setting environment variables

**Part 2: Two deployment paths**
- **Deployment:** With detailed explanation of each YAML file
- **StatefulSet:** With emphasis on differences

**Part 3: Two methods for each path**
- **Declarative:** With YAML files (Infrastructure as Code)
- **Imperative:** With direct CLI commands

**Part 4: Practical testing**
- Detailed curl examples
- Explanation of each endpoint
- Error handling

#### Why the manual guide is important:

1. **Deep understanding:** Understand what each command does
2. **Troubleshooting:** Know how to fix when something doesn't work
3. **Customization:** Can modify for specific needs
4. **Learning:** Understand Kubernetes/OpenShift principles

---

## When to Use Each Tool?

### Use automated scripts if:
- ✅ You want quick deployment
- ✅ It's a demo or presentation
- ✅ You trust the basic settings
- ✅ No special customizations needed

### Use manual guide if:
- 📚 You want to learn and understand
- 🔧 Need specific customizations
- 🐛 There are problems to solve
- 🏗️ Building production environment

### Use testing script if:
- 🧪 Want to verify everything works
- 🔄 Doing CI/CD
- 📊 Need report on system health
- 🚀 Before moving to production

---

## Advanced Tips for Using Scripts

### 1. Customizing scripts for your needs

**Change storage size:**
```bash
# Edit file before running script
sed -i 's/storage: 2Gi/storage: 5Gi/g' infrastructure/k8s/02-mongo-pvc.yaml
```

**Change CPU/Memory resources:**
```bash
# For MongoDB
sed -i 's/memory: "256Mi"/memory: "512Mi"/g' infrastructure/k8s/03-mongo-deployment.yaml
```

### 2. Running scripts with debugging

```bash
# Add verbose output
bash -x ./scripts/deploy.sh your-username

# Save logs to file
./scripts/deploy.sh your-username 2>&1 | tee deployment.log
```

### 3. Using scripts in CI/CD

```yaml
# Example for GitHub Actions
- name: Deploy to OpenShift
  run: |
    # Connect to OpenShift
    oc login --token=${{ secrets.OPENSHIFT_TOKEN }} --server=${{ secrets.OPENSHIFT_SERVER }}
    
    # Run the script
    ./scripts/deploy-statefulset.sh ${{ secrets.DOCKERHUB_USERNAME }}
    
    # Test everything works
    ./scripts/run_api_tests.sh "https://$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')"
```

### 4. Recovery from failures

```bash
# If script failed, clean and try again
oc delete all,pvc,secret,configmap -l app.kubernetes.io/part-of=mongo-loader-app

# Run again
./scripts/deploy.sh your-username
```

### 5. Useful commands after deployment

```bash
# Check status of all components
oc get all -l app.kubernetes.io/part-of=mongo-loader-app

# Get application URL
oc get route -o jsonpath='{.items[0].spec.host}'

# Check logs of all pods
oc logs -l app.kubernetes.io/part-of=mongo-loader-app --all-containers=true
```

---

## Common Script Troubleshooting

### Problem: "Docker build failed"
**Solution:**
```bash
# Check Docker is running
docker version

# Login to Docker Hub
docker login

# Try manual build
docker build -t test-image .
```

### Problem: "OpenShift project not found"
**Solution:**
```bash
# Check connection
oc whoami

# Create new project
oc new-project fastapi-mongo-demo

# Run script again
```

### Problem: "Pod stuck in Pending"
**Solution:**
```bash
# Check what's wrong
oc describe pod <pod-name>

# Check enough resources
oc describe nodes

# If it's PVC, check storage class
oc get storageclass
```

### Problem: "API tests failing"
**Solution:**
```bash
# Check Route exists
oc get routes

# Check pods are running
oc get pods

# Check API logs
oc logs -l app.kubernetes.io/instance=mongo-api
```

The scripts are designed to be robust and give clear error messages, but you can always fall back to the manual guide if something doesn't work as expected.