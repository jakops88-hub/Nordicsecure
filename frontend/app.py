import streamlit as st
import requests
import os
from typing import Optional

# Configuration
API_URL = os.getenv("API_URL", "http://backend:8000")

# Page configuration
st.set_page_config(
    page_title="Nordic Secure RAG",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        padding: 1rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: #10B981;
        color: white;
        border-radius: 0.5rem;
        font-weight: bold;
        text-align: center;
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .license-expired-box {
        background-color: #DC2626;
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        border: 3px solid #991B1B;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)


def check_backend_health() -> bool:
    """Check if the backend is accessible"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False


def show_license_expired_error():
    """Display a prominent license expiration error box"""
    st.markdown("""
        <div class="license-expired-box">
            🔒 Din licens har gått ut. Kontakta Nordic Secure.
        </div>
    """, unsafe_allow_html=True)


def ingest_document(file) -> Optional[dict]:
    """Upload and ingest a PDF document"""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(f"{API_URL}/ingest", files=files, timeout=60)
        
        # Check for license errors
        if response.status_code == 403:
            error_data = response.json()
            if "License Expired" in error_data.get("detail", ""):
                show_license_expired_error()
                return None
            else:
                st.error(f"License error: {error_data.get('detail', 'Unknown error')}")
                return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error ingesting document: {str(e)}")
        return None


def search_documents(query: str) -> Optional[dict]:
    """Search for documents using a query"""
    try:
        response = requests.post(
            f"{API_URL}/search",
            json={"query": query},
            timeout=30
        )
        
        # Check for license errors
        if response.status_code == 403:
            error_data = response.json()
            if "License Expired" in error_data.get("detail", ""):
                show_license_expired_error()
                return None
            else:
                st.error(f"License error: {error_data.get('detail', 'Unknown error')}")
                return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching documents: {str(e)}")
        return None


# Main header
st.markdown('<div class="main-header">🔒 Nordic Secure RAG</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; margin-bottom: 2rem;"><span class="status-badge">System: Offline & Secure</span></div>', unsafe_allow_html=True)

# Sidebar for file upload
with st.sidebar:
    st.markdown('<div class="sidebar-header">📄 Document Upload</div>', unsafe_allow_html=True)
    
    # Backend status check
    backend_status = check_backend_health()
    if backend_status:
        st.success("✅ Backend: Online")
    else:
        st.error("❌ Backend: Offline")
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type=["pdf"],
        help="Upload a PDF document to add it to the secure knowledge base"
    )
    
    if uploaded_file is not None:
        st.info(f"📁 Selected: {uploaded_file.name}")
        
        if st.button("🚀 Ingest Document", use_container_width=True):
            with st.spinner("Processing document..."):
                result = ingest_document(uploaded_file)
                if result:
                    st.success(f"✅ {result.get('message', 'Document ingested successfully')}")
                    st.info(f"Document ID: {result.get('document_id', 'N/A')}")
    
    st.markdown("---")
    
    # API Configuration
    with st.expander("⚙️ API Configuration"):
        st.text_input(
            "API URL",
            value=API_URL,
            disabled=True,
            help="Backend API endpoint (configured via environment variable)"
        )

# Main content area - Chat interface
st.markdown("### 💬 Search & Chat Interface")
st.markdown("Ask questions about your ingested documents. The system will search for relevant information.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Search for relevant documents
    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            search_result = search_documents(prompt)
            
            if search_result and search_result.get("results"):
                results = search_result["results"]
                
                # Format response
                response = f"Found {len(results)} relevant document(s):\n\n"
                
                for idx, doc in enumerate(results, 1):
                    similarity = doc.get("similarity", 0)
                    filename = doc.get("filename", "Unknown")
                    content = doc.get("content", "")
                    
                    # Truncate content for display
                    preview = content[:300] + "..." if len(content) > 300 else content
                    
                    response += f"**{idx}. {filename}** (Similarity: {similarity:.2%})\n\n"
                    response += f"{preview}\n\n"
                    response += "---\n\n"
                
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                error_msg = "No relevant documents found. Please try a different query or upload more documents."
                st.warning(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #6B7280; font-size: 0.875rem;">'
    '🔒 All data processing happens locally. No external connections. Zero data leakage.'
    '</div>',
    unsafe_allow_html=True
)
