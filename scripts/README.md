# Scripts Directory - Deployment and Testing Scripts

🌍 **Language:** **[English](README.md)** | [עברית](README.he.md)

This directory contains all the tools needed for automated deployment and testing of the FastAPI MongoDB application.

## Files in Directory

### 🚀 Automated Deployment Scripts
- **`deploy.sh` / `deploy.bat`** - Standard deployment (Deployment + PVC)
- **`deploy-statefulset.sh` / `deploy-statefulset.bat`** - Advanced deployment (StatefulSet)
- **`run_api_tests.sh`** - End-to-end API testing script

### 📚 Guides
- **`demo_guide.md`** - 📖 **Independent manual deployment guide** - Learn step-by-step deployment without scripts

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

## Tool Details

### 🤖 Automated Deployment Scripts
Two approaches for quick deployment:

1. **Standard approach** (`deploy.sh/bat`):
   - Uses regular Deployment + separate PVC
   - Suitable for development and testing

2. **Advanced approach** (`deploy-statefulset.sh/bat`):
   - Uses StatefulSet + automatic storage management
   - Recommended for production

**Both scripts automatically perform:**
- Build and push Docker image
- Deploy MongoDB and FastAPI to OpenShift
- Create Routes for external access
- Display final URL

### 🧪 Testing Script
`run_api_tests.sh` performs comprehensive validation:
- Test all CRUD operations
- Validate error handling
- Check data persistence
- Verify correct HTTP status codes

### 📚 Manual Guide
`demo_guide.md` is a **completely independent** guide that teaches:
- How to deploy manually without scripts
- Deep understanding of each component
- Two methods: declarative (YAML) and imperative (CLI)
- Manual API testing with `curl`