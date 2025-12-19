# 🚀 Nordic Secure - Deployment Guide for IP-Protected Images

This guide explains how to build, package, and deliver the IP-protected Nordic Secure application to customers.

## 📋 Overview

The Nordic Secure application uses **PyInstaller** to compile the Python backend into a binary executable, protecting the source code from being read or reverse-engineered. The frontend remains as a Streamlit application but can be similarly protected if needed.

## 🔒 IP Protection Strategy

### Backend Protection
- **Multi-stage Docker Build**: Uses PyInstaller to compile Python code to native binary
- **No Source Code**: Final Docker image contains ONLY the compiled binary (no .py files)
- **Hidden Imports**: All dependencies (uvicorn, pgvector, pypdf, passlib) are embedded in the binary
- **Obfuscation**: Binary is not easily reverse-engineered back to source code

### What's Protected
✅ Business logic in `main.py`, `document_service.py`, `database.py`  
✅ API endpoints and routing logic  
✅ Database schema and queries  
✅ Embedding generation logic  

### What Customers Get
- Compiled binary executable (`nordicsecure`)
- Docker images ready to run
- Configuration files (docker-compose.yml)
- Documentation

### What Customers DON'T Get
❌ Python source code (.py files)  
❌ Ability to modify business logic  
❌ Access to proprietary algorithms  

---

## 🛠️ Building the Protected Images

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB free disk space
- Internet connection (for initial build only)

### Step 1: Build All Images

```bash
# Navigate to the project directory
cd /path/to/Nordicsecure

# Build all services (this will take 5-10 minutes on first build)
docker-compose build --no-cache

# Verify the build succeeded
docker-compose images
```

### Step 2: Verify IP Protection

Verify that the backend image does NOT contain Python source files:

```bash
# Check the backend image for .py files
docker run --rm nordicsecure-backend find /app -name "*.py"

# This should return NO results. If it finds .py files, the build failed!
```

### Step 3: Test the Application Locally

Before packaging for delivery, test that everything works:

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Access frontend
# Open browser to http://localhost:8501
```

If everything works correctly, proceed to packaging.

---

## 📦 Packaging for Customer Delivery

### Option A: Save Docker Images to TAR Files (Recommended for USB Delivery)

This method creates portable archive files that can be transferred on USB drives or via file transfer.

```bash
# Save all images to individual tar files
docker save -o nordic-secure-backend.tar nordicsecure-backend:latest
docker save -o nordic-secure-frontend.tar nordicsecure-frontend:latest
docker save -o pgvector.tar ankane/pgvector:latest
docker save -o ollama.tar ollama/ollama:latest

# Check file sizes
ls -lh *.tar

# Expected sizes (approximate):
# nordic-secure-backend.tar  : ~800MB - 1.2GB
# nordic-secure-frontend.tar : ~500MB - 700MB
# pgvector.tar              : ~200MB - 300MB
# ollama.tar                : ~500MB - 800MB
```

### Option B: Create a Single Combined Archive

```bash
# Save all images to a single tar file
docker save -o nordic-secure-complete.tar \
  nordicsecure-backend:latest \
  nordicsecure-frontend:latest \
  ankane/pgvector:latest \
  ollama/ollama:latest

# Compress the archive (optional, saves ~30-40% space)
gzip nordic-secure-complete.tar

# Result: nordic-secure-complete.tar.gz (~1.5GB - 2GB)
```

### Option C: Push to Private Docker Registry

If you have a private Docker registry:

```bash
# Tag images for your registry
docker tag nordicsecure-backend:latest myregistry.com/nordicsecure/backend:latest
docker tag nordicsecure-frontend:latest myregistry.com/nordicsecure/frontend:latest

# Push to registry
docker push myregistry.com/nordicsecure/backend:latest
docker push myregistry.com/nordicsecure/frontend:latest
```

---

## 📤 Delivery Package Contents

Create a delivery package with the following structure:

```
nordic-secure-delivery/
├── images/
│   ├── nordic-secure-backend.tar      # Protected backend binary
│   ├── nordic-secure-frontend.tar     # Streamlit frontend
│   ├── pgvector.tar                   # PostgreSQL with vector support
│   └── ollama.tar                     # Ollama embedding model
├── config/
│   └── docker-compose.yml             # Orchestration configuration
├── docs/
│   ├── CUSTOMER_SETUP_GUIDE.md        # Instructions for customer
│   └── USER_MANUAL.md                 # How to use the application
└── README.txt                         # Quick start instructions
```

### Create the Customer Setup Guide

Create `CUSTOMER_SETUP_GUIDE.md`:

```markdown
# Nordic Secure - Customer Setup Guide

## Loading the Images

1. Copy all .tar files from the images/ folder to your server
2. Load each Docker image:

```bash
docker load -i nordic-secure-backend.tar
docker load -i nordic-secure-frontend.tar
docker load -i pgvector.tar
docker load -i ollama.tar
```

3. Verify images are loaded:

```bash
docker images | grep -E "nordicsecure|pgvector|ollama"
```

## Starting the Application

1. Copy `docker-compose.yml` to your working directory
2. Start all services:

```bash
docker-compose up -d
```

3. Wait for services to initialize (1-2 minutes)
4. Access the application at: http://localhost:8501

## First Time Setup

On first run, pull the embedding model:

```bash
docker-compose exec ollama ollama pull nomic-embed-text
```

This downloads the AI model needed for document processing (~274MB).

## Verification

- Frontend: http://localhost:8501
- Backend API: http://localhost:8000/health
- Database: localhost:5432 (postgres/postgres)

## Stopping the Application

```bash
docker-compose down
```

## Support

Contact: [Your Support Email]
```

---

## 🔐 Security Considerations for Delivery

### Before Delivery
1. ✅ Verify NO .py files in backend image
2. ✅ Test all functionality works
3. ✅ Remove any development/test data from database
4. ✅ Review environment variables (no sensitive defaults)
5. ✅ Ensure logs don't expose sensitive information

### Delivery Methods

**USB Drive** (Most Secure):
- Format: exFAT or NTFS
- Encrypt if possible (BitLocker, VeraCrypt)
- Hand-deliver or use courier service
- Cost: $20-50 for USB drive

**Secure File Transfer**:
- Use encrypted transfer (SFTP, Dropbox with encryption)
- Split large files if needed
- Provide checksum files for verification
- Delete after customer confirms receipt

**Private Cloud Storage**:
- AWS S3 with pre-signed URLs (time-limited)
- Azure Blob Storage with SAS tokens
- Google Cloud Storage with signed URLs
- Set expiration after 7-14 days

### Checksums for Verification

Provide SHA256 checksums for integrity verification:

```bash
# Generate checksums
sha256sum *.tar > checksums.txt

# Customer verifies on their end
sha256sum -c checksums.txt
```

---

## 🚀 Quick Delivery Checklist

- [ ] Build all images with `docker-compose build --no-cache`
- [ ] Verify no .py files in backend image
- [ ] Test application works locally
- [ ] Save images to .tar files
- [ ] Generate SHA256 checksums
- [ ] Create customer setup guide
- [ ] Package all files in delivery folder
- [ ] Test customer setup instructions
- [ ] Deliver via chosen method
- [ ] Provide customer support contact

---

## 🔧 Troubleshooting

### Build Fails
```bash
# Clean Docker cache and rebuild
docker system prune -a
docker-compose build --no-cache
```

### Image Too Large
```bash
# Compress images
gzip *.tar

# Or use docker image optimization
docker image prune
```

### Customer Can't Load Images
```bash
# Ensure Docker version compatibility
docker --version  # Should be 20.10 or higher

# Load images one by one to identify issues
docker load -i backend.tar -v
```

---

## 📞 Support

For questions about deployment or delivery:
- Technical Support: [Your Email]
- Documentation: [Your Wiki/Docs URL]
- Emergency: [Your Phone Number]

---

## 📝 Notes

- **Build Time**: First build takes 10-15 minutes due to PyInstaller compilation
- **Image Sizes**: Total package size ~2-3GB (compressed: ~1.5-2GB)
- **Customer Requirements**: Docker 20.10+, Docker Compose 1.29+, 8GB RAM, 20GB disk
- **License**: Ensure customer has valid license before delivery
- **Updates**: Provide update mechanism (rebuild images, redistribute)

---

**Last Updated**: 2025-12-19
**Version**: 1.0.0
**Protected**: ✅ PyInstaller Binary Compilation
