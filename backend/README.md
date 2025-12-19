# NordicSecure Backend

Nordic Secure Private, offline RAG infrastructure for regulated industries. A sovereign AI engine that runs 100% locally using sentence-transformers/Ollama and pgvector to ensure zero data leakage.

## Architecture

This backend is a refactored and migrated implementation combining functionality from three previous projects:

1. **pdf-api**: PDF parsing, OCR, and table extraction
2. **Long-Term-Memory-API**: Vector embeddings and storage
3. **AgentAudit-AI-Grounding-Reliability-Check**: AI grounding and validation

## Features

### DocumentService

The core `DocumentService` class provides:

#### PDF Parsing (`parse_pdf`)
- **Text Extraction**: Extracts text from native PDFs using PyPDF2
- **OCR Fallback**: Automatically detects scanned PDFs and uses Tesseract OCR
- **Table Detection**: Identifies and extracts tables (pipe-separated, tab-separated, or multi-space columns)
- **Invoice Field Extraction**: Detects and extracts:
  - Invoice numbers
  - Dates (invoice date, due date)
  - Monetary amounts (total, subtotal, VAT)
  - Currency
  - Supplier and customer names
- **Confidence Scores**: Provides confidence scores for each extracted field
- **Language Detection**: Detects Swedish or English content

#### Document Storage (`store_document`)
- **Vector Embeddings**: Generates semantic embeddings using sentence-transformers
- **Local Processing**: Runs 100% locally for data sovereignty
- **pgvector Storage**: Stores documents with embeddings in PostgreSQL with pgvector extension
- **Metadata Support**: Stores arbitrary metadata with each document

## Installation

### Prerequisites

1. **PostgreSQL with pgvector extension**:
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Install pgvector extension
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable extension in your database
psql -U postgres -d nordicsecure -c "CREATE EXTENSION vector;"
```

2. **Tesseract OCR** (optional, for scanned PDFs):
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

3. **System dependencies for pdf2image**:
```bash
sudo apt-get install poppler-utils
```

### Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the `backend` directory:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nordicsecure
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional: Use Ollama for local embeddings
USE_OLLAMA=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=nomic-embed-text

# Logging
LOG_LEVEL=INFO
```

### Database Setup

```sql
-- Create database
CREATE DATABASE nordicsecure;

-- Connect to database
\c nordicsecure

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- The documents table will be created automatically on first use
-- But you can create it manually:
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    embedding vector(384),  -- Dimension depends on your embedding model
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

## Usage Examples

### Basic PDF Parsing

```python
from app.services import DocumentService

# Initialize service
service = DocumentService()

# Parse a PDF file
with open("invoice.pdf", "rb") as f:
    pdf_bytes = f.read()

result = service.parse_pdf(pdf_bytes, filename="invoice.pdf")

# Access extracted data
print(f"Pages: {result['metadata']['pages_count']}")
print(f"Language: {result['metadata']['detected_language']}")
print(f"Full text: {result['raw_text'][:200]}...")

# Access invoice fields
print(f"\nInvoice Number: {result['key_values']['invoice_number']}")
print(f"  Confidence: {result['key_values_confidence']['invoice_number']}")

print(f"\nTotal Amount: {result['key_values']['total_amount']}")
print(f"  Currency: {result['key_values']['currency']}")

# Access extracted tables
for i, table in enumerate(result['tables']):
    print(f"\nTable {i+1} (Page {table['page_number']}):")
    for row in table['rows'][:3]:  # First 3 rows
        print(f"  {row}")
```

### Document Storage with Embeddings

```python
from app.services import DocumentService
from app.config import Config

# Initialize service with database configuration
service = DocumentService(
    embedding_model="all-MiniLM-L6-v2",
    db_config=Config.get_db_config()
)

# Parse PDF
with open("document.pdf", "rb") as f:
    result = service.parse_pdf(f.read())

# Store document with embeddings
metadata = {
    "filename": "document.pdf",
    "user_id": "user123",
    "category": "invoice",
    "extracted_fields": result['key_values']
}

storage_result = service.store_document(
    text=result['raw_text'],
    metadata=metadata
)

print(f"Stored document ID: {storage_result['document_id']}")
print(f"Embedding dimension: {storage_result['embedding_dim']}")
print(f"Stored at: {storage_result['stored_at']}")

# Don't forget to close the connection
service.close()
```

### Using with Ollama (Local Embeddings)

For complete data sovereignty, use Ollama for local embeddings:

```python
from app.services import DocumentService
from app.config import Config

# This will use Ollama if USE_OLLAMA=true in .env
config = Config.get_embedding_config()

service = DocumentService(
    embedding_model=config['ollama_model'] if config['use_ollama'] else config['embedding_model'],
    db_config=Config.get_db_config()
)

# Use as normal - embeddings are generated locally
```

### Complete Pipeline Example

```python
import logging
from app.services import DocumentService
from app.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize service
service = DocumentService(
    embedding_model="all-MiniLM-L6-v2",
    db_config=Config.get_db_config()
)

try:
    # 1. Parse PDF
    with open("invoice.pdf", "rb") as f:
        parse_result = service.parse_pdf(f.read(), filename="invoice.pdf")
    
    print(f"✓ Parsed {parse_result['metadata']['pages_count']} pages")
    print(f"✓ Extracted {len(parse_result['tables'])} tables")
    
    # 2. Store with embeddings
    storage_result = service.store_document(
        text=parse_result['raw_text'],
        metadata={
            "filename": "invoice.pdf",
            "invoice_number": parse_result['key_values']['invoice_number'],
            "total_amount": parse_result['key_values']['total_amount'],
            "currency": parse_result['key_values']['currency']
        }
    )
    
    print(f"✓ Stored document ID: {storage_result['document_id']}")
    print(f"✓ Embedding dimension: {storage_result['embedding_dim']}")
    
finally:
    service.close()
```

## API Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py          # Configuration management
│   └── services/
│       ├── __init__.py
│       └── document_service.py # Core DocumentService class
└── requirements.txt
```

## Testing

Create a test file to validate the implementation:

```python
# test_document_service.py
import os
from app.services import DocumentService
from app.config import Config

def test_parse_pdf():
    """Test PDF parsing functionality."""
    service = DocumentService()
    
    # Test with a sample PDF (create one or use existing)
    with open("test_invoice.pdf", "rb") as f:
        result = service.parse_pdf(f.read())
    
    assert result['raw_text']
    assert result['metadata']['pages_count'] > 0
    assert 'key_values' in result
    
    print("✓ PDF parsing test passed")

def test_store_document():
    """Test document storage with embeddings."""
    service = DocumentService(
        db_config=Config.get_db_config()
    )
    
    try:
        result = service.store_document(
            text="This is a test document for vector storage.",
            metadata={"test": True}
        )
        
        assert result['document_id']
        assert result['embedding_dim'] > 0
        
        print("✓ Document storage test passed")
    finally:
        service.close()

if __name__ == "__main__":
    test_parse_pdf()
    test_store_document()
    print("\n✓ All tests passed!")
```

## Performance Considerations

### Embedding Models

- **all-MiniLM-L6-v2** (384 dimensions): Fast, good quality, recommended for most use cases
- **all-mpnet-base-v2** (768 dimensions): Higher quality, slower
- **Ollama nomic-embed-text**: Local embeddings for complete data sovereignty

### Database Indexing

For production deployments with large document collections, create appropriate indexes:

```sql
-- For exact search
CREATE INDEX idx_documents_metadata ON documents USING gin(metadata);

-- For vector similarity search (adjust lists parameter based on dataset size)
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- For faster inserts with periodic VACUUM ANALYZE
CREATE INDEX ON documents(created_at);
```

## Security & Privacy

This implementation prioritizes data sovereignty:

1. **100% Local Processing**: All PDF parsing, OCR, and embeddings run locally
2. **No External API Calls**: No data sent to OpenAI, Google, or other cloud services
3. **Offline Operation**: Works completely offline once models are downloaded
4. **pgvector Storage**: Data stored in your own PostgreSQL instance
5. **Regulated Industry Ready**: Suitable for GDPR, HIPAA, and other compliance requirements

## Troubleshooting

### OCR Issues

If OCR is not working:
```bash
# Verify Tesseract installation
tesseract --version

# Install language data if needed
sudo apt-get install tesseract-ocr-swe  # Swedish
sudo apt-get install tesseract-ocr-eng  # English
```

### pgvector Issues

If vector operations fail:
```sql
-- Verify pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check vector type is available
SELECT typname FROM pg_type WHERE typname = 'vector';
```

### Memory Issues

For large PDFs or batch processing:
- Increase available RAM
- Process documents in batches
- Use smaller embedding models
- Enable swap space on Linux

## License

This is a refactored implementation combining logic from multiple open-source projects.
Ensure compliance with original project licenses when using in production.

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- All functions have docstrings
- Tests are included for new features
- Data sovereignty principles are maintained
