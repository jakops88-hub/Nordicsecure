# 🚀 Nordic Secure - Quick Start Guide

## For First-Time Users

This guide will help you get Nordic Secure up and running in minutes.

---

## 📋 Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Docker installed (version 20.10 or higher)
- [ ] Docker Compose installed (version 1.29 or higher)
- [ ] At least 8GB RAM available
- [ ] At least 20GB free disk space
- [ ] Internet connection (for initial setup only)

Check your versions:
```bash
docker --version
docker compose version
```

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Clone and Navigate
```bash
git clone https://github.com/jakops88-hub/Nordicsecure.git
cd Nordicsecure
```

### Step 2: Start All Services
```bash
# Build and start all containers
docker compose up -d

# This will:
# - Start PostgreSQL database with pgvector
# - Start Ollama AI service
# - Build and start the protected backend
# - Build and start the Streamlit frontend
```

### Step 3: Download AI Model (First Time Only)
```bash
# Wait 30 seconds for services to start, then:
docker compose exec ollama ollama pull nomic-embed-text

# This downloads the embedding model (~274MB)
# Takes 1-2 minutes depending on connection speed
```

### Step 4: Access the Application
```bash
# Frontend (Web UI): 
open http://localhost:8501

# Backend API:
open http://localhost:8000/health
```

**That's it! You're ready to use Nordic Secure! 🎉**

---

## 🎯 Using Nordic Secure

### Upload Your First Document

1. **Open the Frontend**: Navigate to http://localhost:8501
2. **Look at the Sidebar** (left side of the screen)
3. **Click "Browse files"** and select a PDF document
4. **Click "🚀 Ingest Document"**
5. **Wait** for processing (10-30 seconds depending on document size)
6. **Success!** You'll see a confirmation with a Document ID

### Search Your Documents

1. **Look at the Main Area** (center of the screen)
2. **Type a question** in the chat input at the bottom
   - Example: "What is the retention policy?"
   - Example: "Show me information about data protection"
3. **Press Enter** or click the send button
4. **View Results** with:
   - Similarity scores (how relevant each document is)
   - Document excerpts with context
   - Source document filenames

### Chat History

- All your queries and results are saved in the session
- Scroll up to see previous searches
- Clear by refreshing the page

---

## 🔍 Verification (Optional)

Want to verify everything is working correctly?

```bash
# Run the verification script
./verify_deployment.sh

# Should show all green checkmarks ✓
```

---

## 📊 Service Status

Check if all services are running:

```bash
docker compose ps
```

Expected output:
- ✅ `db` - running (PostgreSQL)
- ✅ `ollama` - running (AI embeddings)
- ✅ `backend` - running (FastAPI - Port 8000)
- ✅ `frontend` - running (Streamlit - Port 8501)

---

## 🛠️ Common Tasks

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f frontend
docker compose logs -f backend
```

### Restart Services
```bash
# Restart everything
docker compose restart

# Restart specific service
docker compose restart frontend
```

### Stop Services
```bash
# Stop but keep data
docker compose stop

# Stop and remove containers (keeps data volumes)
docker compose down

# Stop and remove EVERYTHING including data
docker compose down -v
```

### Update the Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build
```

---

## 🐛 Troubleshooting

### Frontend won't start
```bash
# Check logs
docker compose logs frontend

# Common fix: Rebuild
docker compose up -d --build frontend
```

### Backend returns errors
```bash
# Check if database is ready
docker compose logs db

# Check backend logs
docker compose logs backend

# Restart backend
docker compose restart backend
```

### Can't upload PDFs
```bash
# Check backend is running
curl http://localhost:8000/health

# Should return: {"status":"healthy",...}
```

### Search returns no results
```bash
# Check if documents were ingested
docker compose logs backend | grep "ingested"

# Check if Ollama model is downloaded
docker compose exec ollama ollama list

# Should show: nomic-embed-text
```

### Services use too much memory
```bash
# Check resource usage
docker stats

# Adjust in docker-compose.yml if needed
# (add memory limits under each service)
```

---

## 🔒 Security Notes

- ✅ All processing happens **locally** - no internet required after setup
- ✅ No data is sent to external services
- ✅ Database is only accessible from within Docker network
- ✅ Frontend only communicates with local backend
- ✅ Perfect for sensitive/regulated data

---

## 📚 Next Steps

### Learn More
- Read `README.md` for detailed API documentation
- Check `DEPLOY_GUIDE.md` for customer deployment
- Review `IMPLEMENTATION_SUMMARY.md` for technical details

### Advanced Usage
- Upload multiple documents
- Fine-tune search queries
- Adjust similarity thresholds
- Customize the frontend UI
- Add authentication (not included by default)

### Development
```bash
# Enable development mode (edit files live)
# Edit docker-compose.yml:
# Under frontend, add:
#   volumes:
#     - ./frontend:/app

docker compose up -d --build
```

---

## 💡 Tips & Best Practices

1. **Document Quality**: Better quality PDFs = better results
   - Clear text (not scanned/blurry)
   - Well-structured documents
   - Swedish documents work well (OCR support included)

2. **Query Phrasing**: Ask natural questions
   - ✅ "What are the data retention policies?"
   - ✅ "Show me information about GDPR compliance"
   - ❌ Don't use keywords only: "retention GDPR data"

3. **Result Interpretation**:
   - Similarity > 0.70 = Very relevant
   - Similarity > 0.50 = Moderately relevant
   - Similarity < 0.50 = May not be relevant

4. **Performance**:
   - First upload is slower (model initialization)
   - Subsequent uploads are faster
   - Search is usually fast (<2 seconds)

---

## ❓ Getting Help

### Documentation
- `README.md` - General overview
- `DEPLOY_GUIDE.md` - Deployment guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details

### Logs
Always check logs first:
```bash
docker compose logs -f [service-name]
```

### Health Checks
```bash
# Backend API
curl http://localhost:8000/health

# Database
docker compose exec db pg_isready -U postgres

# Ollama
docker compose exec ollama ollama list
```

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs: `docker compose logs`
3. Verify all services are running: `docker compose ps`
4. Run verification: `./verify_deployment.sh`

---

**🎉 Enjoy using Nordic Secure!**

*A secure, local, offline RAG solution for sensitive documents.*
