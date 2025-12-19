# Nordicsecure

Nordic Secure Private, offline RAG infrastructure for regulated industries. A sovereign AI engine that runs 100% locally using Ollama and pgvector to ensure zero data leakage.

## Overview

This project provides a complete backend infrastructure for document processing and semantic search with complete data sovereignty. It combines functionality from three previous projects:

1. **pdf-api**: PDF parsing, OCR, and table extraction
2. **Long-Term-Memory-API**: Vector embeddings and storage with pgvector
3. **AgentAudit-AI-Grounding-Reliability-Check**: AI grounding and reliability validation

## Features

- **PDF Parsing**: Extract text, tables, and invoice fields from PDF documents
- **OCR Support**: Automatic fallback to OCR for scanned documents
- **Vector Embeddings**: Generate semantic embeddings using sentence-transformers or Ollama
- **Local Processing**: 100% local operation for complete data sovereignty
- **pgvector Storage**: Efficient vector similarity search in PostgreSQL
- **Compliance Ready**: GDPR, HIPAA, SOC 2, ISO 27001 compliant by design

## Getting Started

See the [backend README](backend/README.md) for detailed installation and usage instructions.

### Quick Start

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your database credentials

# Run examples
python example_usage.py
```

## Documentation

- [Backend Documentation](backend/README.md) - Complete setup and usage guide
- [Example Usage](backend/example_usage.py) - Code examples and demonstrations
