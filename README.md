# Nordicsecure

Nordic Secure Private, offline RAG infrastructure for regulated industries. A sovereign AI engine that runs 100% locally using Ollama and pgvector to ensure zero data leakage.

## Features

- **🎨 Streamlit Frontend**: User-friendly web interface for document upload and chat-based search
- **PDF Document Ingestion**: Upload PDF files with automatic text extraction using PyPDF2 and OCR (Tesseract)
- **Semantic Search**: Search documents using natural language queries with embeddings
- **100% Local**: All processing happens locally using Ollama for embeddings
- **Swedish OCR Support**: Full support for Swedish language documents with tesseract-ocr-swe
- **Vector Search**: Fast similarity search using pgvector with cosine similarity
- **🔒 IP Protection**: Backend compiled to binary using PyInstaller to protect source code
- **Scalable**: Docker-based architecture with PostgreSQL and Ollama

## Architecture

- **Frontend**: Streamlit web application with chat interface and file upload
- **Backend**: FastAPI REST API compiled to binary (IP protected)
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **Embeddings**: Ollama (nomic-embed-text model) for generating document embeddings
- **OCR**: Tesseract OCR with Swedish language support for scanning PDF documents

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/jakops88-hub/Nordicsecure.git
cd Nordicsecure
```

2. Start all services:
```bash
docker-compose up -d
```

3. Wait for Ollama to pull the embedding model (first time only):
```bash
docker-compose exec ollama ollama pull nomic-embed-text
```

4. Access the application:
- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000

## Using the Application

### Web Interface (Recommended)

1. Open http://localhost:8501 in your browser
2. Use the sidebar to upload PDF documents
3. Use the chat interface to search your documents
4. View results with similarity scores and document excerpts

### API Endpoints (Advanced)

### POST /ingest

Upload and ingest a PDF document.

**Request:**
```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "document_id": 1,
  "filename": "document.pdf",
  "message": "Document ingested successfully"
}
```

### POST /search

Search for documents using a text query.

**Request:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "what is the policy on data retention?"}'
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "filename": "policy.pdf",
      "content": "...",
      "similarity": 0.85
    }
  ]
}
```

### GET /

Health check endpoint.

### GET /health

Extended health check endpoint.

## Development

### Project Structure

```
Nordicsecure/
├── frontend/
│   ├── app.py               # Streamlit web interface
│   ├── requirements.txt     # Frontend dependencies
│   └── Dockerfile          # Frontend container
├── backend/
│   ├── main.py              # FastAPI application with endpoints
│   ├── database.py          # Database models and configuration
│   ├── document_service.py  # Document processing and search service
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Backend container with PyInstaller (IP protected)
├── docker-compose.yml       # Docker orchestration
├── DEPLOY_GUIDE.md         # Deployment and customer delivery guide
└── README.md
```

### Running Locally

1. Start the services:
```bash
docker-compose up --build
```

2. View logs:
```bash
docker-compose logs -f backend
```

3. Stop services:
```bash
docker-compose down
```

## Technical Details

### OCR Support

The backend includes Tesseract OCR with Swedish language support. The Dockerfile installs:
- `tesseract-ocr`: The OCR engine
- `tesseract-ocr-swe`: Swedish language data
- `poppler-utils`: For PDF to image conversion

### Embedding Model

Uses the `nomic-embed-text` model from Ollama, which generates 768-dimensional embeddings optimized for semantic search.

### Database Schema

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768)
);
```

## Security

- All data stays local - no external API calls
- No data leakage to cloud services
- Suitable for regulated industries requiring data sovereignty
- Database and Ollama run in isolated Docker containers
- **Backend source code protected** - Compiled to binary using PyInstaller

## Deployment to Customers

For instructions on building IP-protected images and delivering to customers, see **[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)**.

The backend is compiled to a binary executable to protect proprietary code when delivering to customers.

## License

MIT
