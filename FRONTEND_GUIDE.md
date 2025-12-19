# 🎨 Nordic Secure Frontend - Features & User Guide

## Overview

The Nordic Secure frontend is a modern, user-friendly Streamlit web application designed for lawyers and professionals working with sensitive documents. It provides an intuitive interface for document management and semantic search.

---

## 🌟 Key Features

### 1. Modern User Interface
- **Clean Design**: Professional Nordic-themed interface
- **Responsive Layout**: Works on desktop browsers
- **Color-Coded Status**: Visual indicators for system health
- **Intuitive Navigation**: Sidebar for actions, main area for interaction

### 2. Document Management
- **PDF Upload**: Drag-and-drop or browse for files
- **File Validation**: Ensures only PDF files are uploaded
- **Progress Feedback**: Real-time status during upload
- **Document Tracking**: Each document gets a unique ID
- **Batch Processing**: Upload multiple documents sequentially

### 3. Intelligent Search
- **Chat Interface**: Natural conversation-style interaction
- **Semantic Search**: Understands meaning, not just keywords
- **Relevance Scoring**: Shows how well each result matches your query
- **Context Preview**: See relevant excerpts from documents
- **Multi-Document Search**: Searches across all ingested documents

### 4. Security & Privacy
- **Offline Operation**: No external connections after setup
- **Local Processing**: All data stays on your infrastructure
- **Secure Badge**: Prominent "System: Offline & Secure" indicator
- **No Data Leakage**: Zero communication with cloud services

### 5. System Health Monitoring
- **Backend Status**: Real-time connection indicator
- **Visual Feedback**: Green checkmark (online) / Red X (offline)
- **Automatic Checks**: Polls backend health every page load

---

## 🖥️ User Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│                   🔒 Nordic Secure RAG                      │
│              System: Offline & Secure                       │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  SIDEBAR     │         MAIN CHAT AREA                       │
│              │                                              │
│ 📄 Document  │  💬 Search & Chat Interface                  │
│    Upload    │                                              │
│              │  [Previous messages shown here]              │
│ ✅ Backend:  │                                              │
│    Online    │  User: What is the policy?                   │
│              │                                              │
│ [Browse...]  │  Assistant: Found 2 documents...             │
│              │  1. policy.pdf (85% match)                   │
│ [🚀 Ingest]  │     "The retention policy..."                │
│              │                                              │
│ ─────────    │  ─────────────────────────────               │
│              │                                              │
│ ⚙️ API       │  [Type your question here...]                │
│ Configuration│                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
         All data processing happens locally
```

---

## 📖 Feature Details

### Document Upload Panel (Sidebar)

#### Backend Status Indicator
- **Purpose**: Shows if the backend API is reachable
- **States**:
  - ✅ Green "Backend: Online" - Ready to use
  - ❌ Red "Backend: Offline" - Check services

#### File Uploader
- **Accepted Format**: PDF only
- **File Size**: Limited by backend configuration (typically 10-50MB)
- **Process**:
  1. Click "Browse files" or drag PDF onto button
  2. File name appears: "📁 Selected: document.pdf"
  3. Click "🚀 Ingest Document"
  4. Processing indicator appears
  5. Success message with Document ID

#### Example Upload Flow
```
User Action          System Response
───────────         ────────────────
Select PDF    →     "📁 Selected: contract.pdf"
Click Ingest  →     "Processing document..."
Wait 10-30s   →     "✅ Document ingested successfully"
                    "Document ID: 42"
```

### Chat Interface (Main Area)

#### Search Input
- **Location**: Bottom of main area
- **Placeholder**: "Ask a question about your documents..."
- **Input Type**: Text (supports natural language)
- **Submit**: Press Enter or click send icon

#### Message Display
- **User Messages**: Right-aligned, distinct styling
- **Assistant Responses**: Left-aligned with results
- **History**: Persists during session (cleared on refresh)

#### Search Results Format
```
Found 2 relevant document(s):

**1. employment-policy.pdf** (Similarity: 87.32%)

The retention policy for employee documents is 7 years 
from the date of termination. This includes all contracts,
performance reviews, and disciplinary records...

---

**2. data-protection-guidelines.pdf** (Similarity: 76.45%)

All personal data must be retained according to GDPR 
guidelines, with a maximum retention period of 5 years
unless required by law...

---
```

#### Similarity Score Interpretation
- **90-100%**: Excellent match - Highly relevant
- **70-89%**: Good match - Very relevant
- **50-69%**: Fair match - Moderately relevant
- **30-49%**: Weak match - Possibly relevant
- **0-29%**: Poor match - Likely not relevant

---

## 🎯 Usage Scenarios

### Scenario 1: Legal Research
**Task**: Find information about data retention policies

1. **Upload**: Ingest policy documents via sidebar
2. **Query**: "What are our data retention requirements?"
3. **Review**: Check similarity scores and excerpts
4. **Follow-up**: "Are there exceptions for legal holds?"

### Scenario 2: Contract Review
**Task**: Search for specific clauses across multiple contracts

1. **Upload**: Upload all contract PDFs
2. **Query**: "Show me non-compete clauses"
3. **Compare**: Review results from different contracts
4. **Export**: Copy relevant text for analysis

### Scenario 3: Compliance Check
**Task**: Verify GDPR compliance across documents

1. **Upload**: Upload compliance documents
2. **Query**: "How do we handle data subject requests?"
3. **Verify**: Check consistency across documents
4. **Document**: Save findings for audit

---

## ⚙️ Configuration

### API URL Configuration
- **Location**: Sidebar → "⚙️ API Configuration" (expandable)
- **Default**: `http://backend:8000`
- **Environment Variable**: `API_URL`
- **Production**: Usually no change needed
- **Development**: May need `http://localhost:8000`

### Changing API URL
```bash
# In docker-compose.yml, under frontend service:
environment:
  API_URL: http://backend:8000  # Change if needed
```

---

## 🔧 Customization

### Changing Colors/Styling
Edit `frontend/app.py`, find the CSS section:

```python
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;  /* Change this color */
    }
    .status-badge {
        background-color: #10B981;  /* Change this color */
    }
    </style>
""", unsafe_allow_html=True)
```

### Adjusting Results Count
Edit `frontend/app.py`, find the search call:

```python
# Currently defaults to 5 results
# Backend controls this via limit parameter
# To change, modify the search_documents call in document_service.py
```

### Customizing Messages
All user-facing messages can be edited in `frontend/app.py`:
- Success messages
- Error messages
- Status indicators
- Help text

---

## 🎨 Theming

### Current Theme
- **Primary Color**: Nordic Blue (#1E3A8A)
- **Success Color**: Green (#10B981)
- **Layout**: Wide mode
- **Sidebar**: Expanded by default

### Custom Theme
Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1E3A8A"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F3F4F6"
textColor = "#1F2937"
font = "sans serif"
```

---

## 🔒 Security Features

### Data Privacy
- **No External Calls**: All processing local
- **No Analytics**: No tracking or telemetry
- **Session Isolation**: Each user session is independent
- **Memory Safety**: Chat history only in browser memory

### Network Security
- **Internal Network**: Frontend talks only to backend
- **No Internet**: No external dependencies after setup
- **Docker Network**: Isolated container network

### Access Control
- **Default**: No authentication (local use assumed)
- **Add Authentication**: Can integrate Streamlit auth
- **Network Security**: Use firewall/VPN for production

---

## 📊 Performance

### Load Times
- **Initial Load**: 2-3 seconds
- **Document Upload**: 10-30 seconds (depends on size)
- **Search Query**: 1-2 seconds
- **Backend Health Check**: <1 second

### Optimization Tips
1. **Keep PDFs under 10MB** for faster uploads
2. **Use specific queries** for better results
3. **Clear browser cache** if UI is slow
4. **Restart frontend** if memory issues occur

---

## 🐛 Troubleshooting

### Frontend Won't Load
```bash
# Check if container is running
docker compose ps frontend

# Check logs
docker compose logs frontend

# Restart
docker compose restart frontend
```

### Can't Upload Files
- **Check**: Backend status indicator shows green
- **Verify**: Backend is actually running: `curl http://localhost:8000/health`
- **Logs**: Check backend logs for errors

### Search Returns Nothing
- **Verify**: Documents were successfully ingested
- **Check**: Embedding model is downloaded
- **Try**: Different query phrasing

### UI Looks Broken
- **Clear**: Browser cache and cookies
- **Try**: Different browser (Chrome, Firefox)
- **Rebuild**: `docker compose up -d --build frontend`

---

## 💡 Tips & Best Practices

### Document Upload
1. Upload documents one at a time for better tracking
2. Wait for confirmation before uploading next document
3. Use descriptive filenames (shown in search results)
4. Keep PDFs text-based (not scanned images) when possible

### Search Queries
1. Use complete questions: "What is the policy on X?"
2. Be specific: "Show me information about employee benefits"
3. Include context: "What does the contract say about termination?"
4. Try variations if first query doesn't work well

### Result Interpretation
1. Check similarity scores first
2. Read the excerpt in context
3. Note the source document name
4. Try follow-up queries for clarification

---

## 🚀 Advanced Usage

### Batch Operations
For uploading many documents:
1. Upload first document
2. Wait for confirmation
3. Upload next document
4. Repeat

*(Future enhancement: Could add batch upload feature)*

### Export Results
Currently:
- Copy text from chat window
- Take screenshots
- Save chat history manually

*(Future enhancement: Could add export button)*

### Integration with Other Tools
The frontend can be extended to:
- Send results to external systems
- Generate reports
- Export to PDF/Word
- Integrate with document management systems

---

## 📝 Future Enhancements

Potential improvements (not currently implemented):
- [ ] User authentication
- [ ] Document management (delete, list all)
- [ ] Advanced filters (by date, type, etc.)
- [ ] Export functionality
- [ ] Batch upload
- [ ] Document preview
- [ ] Citation tracking
- [ ] User preferences

---

**For technical details about implementation, see `IMPLEMENTATION_SUMMARY.md`**

**For deployment to customers, see `DEPLOY_GUIDE.md`**

**For quick setup, see `QUICKSTART.md`**
