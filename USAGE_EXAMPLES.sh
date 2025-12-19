#!/bin/bash
# Example usage script for Nordicsecure API

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo -e "${BLUE}=== Nordicsecure API Usage Examples ===${NC}\n"

# 1. Health check
echo -e "${GREEN}1. Health Check${NC}"
echo "Command: curl http://localhost:8000/health"
echo ""

# 2. Ingest a document
echo -e "${GREEN}2. Ingest a PDF Document${NC}"
echo "Command: curl -X POST \"${API_URL}/ingest\" \\"
echo "  -F \"file=@/path/to/document.pdf\""
echo ""
echo "Expected Response:"
echo '{'
echo '  "document_id": 1,'
echo '  "filename": "document.pdf",'
echo '  "message": "Document ingested successfully"'
echo '}'
echo ""

# 3. Search for documents
echo -e "${GREEN}3. Search for Documents${NC}"
echo "Command: curl -X POST \"${API_URL}/search\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"query\": \"what is the policy on data retention?\"}'"
echo ""
echo "Expected Response:"
echo '{'
echo '  "results": ['
echo '    {'
echo '      "id": 1,'
echo '      "filename": "policy.pdf",'
echo '      "content": "...(document text)...",'
echo '      "similarity": 0.85'
echo '    }'
echo '  ]'
echo '}'
echo ""

# 4. API Documentation
echo -e "${GREEN}4. Access Interactive API Documentation${NC}"
echo "Open in browser: ${API_URL}/docs"
echo ""

echo -e "${BLUE}=== Setup Instructions ===${NC}"
echo ""
echo "1. Start all services:"
echo "   docker-compose up -d"
echo ""
echo "2. Wait for services to be ready (check with docker-compose ps)"
echo ""
echo "3. Pull the Ollama embedding model (first time only):"
echo "   docker-compose exec ollama ollama pull nomic-embed-text"
echo ""
echo "4. Test the API using the commands above"
echo ""
