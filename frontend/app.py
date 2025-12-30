# ==============================================================================
# IRON DOME: SECURITY & OFFLINE ENFORCEMENT
# Must be at the very top before ANY library imports to disable telemetry
# ==============================================================================
import os

# Disable LangChain telemetry and tracing
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_API_KEY"] = ""

# Disable SCARF analytics (used by some ML libraries)
os.environ["SCARF_NO_ANALYTICS"] = "true"

# Disable HuggingFace telemetry
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Disable Streamlit telemetry (redundant with config.toml but ensures it)
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

# ==============================================================================
# Standard imports after telemetry blocking
# ==============================================================================
import streamlit as st
import requests
import pandas as pd
import traceback
import csv
from datetime import datetime, timezone

# Backend URL from environment variable or default
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# Timeout for long-running batch operations (in seconds)
TRIAGE_TIMEOUT = int(os.getenv("TRIAGE_TIMEOUT", "3600"))  # 1 hour default

st.set_page_config(page_title="Nordic Secure", page_icon="🔐", layout="wide")

# Professional CSS styling - Clean Corporate Design
st.markdown("""
<style>
    /* Hide Streamlit default elements using data-testid for reliability */
    [data-testid="stHeader"] {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    section[data-testid="stSidebar"] > div:first-child {padding-top: 1rem;}
    
    /* Fallback for older Streamlit versions */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Clean corporate background */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Main content area styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Button styling - minimal and consistent */
    .stButton>button {
        background-color: #2E5090;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: background-color 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #1E3A6F;
        border: none;
    }
    
    /* Input fields - clean borders */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        border: 1px solid #D1D5DB;
        border-radius: 4px;
        padding: 0.5rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #E5E7EB;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
        color: #6B7280;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        color: #2E5090;
        border-bottom: 2px solid #2E5090;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1F2937;
        font-weight: 600;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 4px;
        font-weight: 500;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #D1D5DB;
        border-radius: 8px;
        padding: 1rem;
        background-color: #F9FAFB;
    }
    
    /* Success/Error/Info messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 4px;
        padding: 1rem;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2E5090;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# AUDIT LOGGING FUNCTIONALITY
# ==============================================================================
AUDIT_LOG_FILE = "audit_log.csv"

def log_query_to_audit(user: str, query: str, result_count: int):
    """
    Log user queries to audit_log.csv for compliance.
    
    Args:
        user: Username or identifier
        query: The search query text
        result_count: Number of results returned
    """
    try:
        from pathlib import Path
        log_path = Path(AUDIT_LOG_FILE)
        file_exists = log_path.exists()
        
        with open(log_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow(['Timestamp', 'User', 'Query', 'Result_Count'])
            
            # Write audit entry
            timestamp = datetime.now().isoformat()
            writer.writerow([timestamp, user, query, result_count])
    except Exception as e:
        # Silently fail if audit logging fails - don't disrupt user experience
        pass


# ==============================================================================
# STARTUP NETWORK CHECK
# ==============================================================================
def check_network_connection():
    """
    Check if network connection is available.
    
    Returns:
        bool: True if network is accessible, False otherwise
    """
    try:
        # Try to reach a common site with HTTPS (secure)
        response = requests.get("https://www.google.com", timeout=2)
        return response.status_code == 200
    except:
        return False


def check_license():
    """
    Check license status with backend.
    
    Returns:
        dict: License status with 'valid' and 'message' keys
    """
    try:
        response = requests.get(f"{BACKEND_URL}/license/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"valid": False, "message": "Could not verify license"}
    except requests.exceptions.Timeout:
        return {"valid": False, "message": "License check timed out"}
    except requests.exceptions.ConnectionError:
        return {"valid": False, "message": "Cannot connect to backend"}
    except requests.exceptions.RequestException as e:
        return {"valid": False, "message": f"License check error: {str(e)}"}

def activate_license(license_key: str):
    """
    Activate a license key.
    
    Args:
        license_key: The license key to activate
        
    Returns:
        dict: Activation result with 'success' and 'message' keys
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/license/activate",
            json={"license_key": license_key},
            timeout=5
        )
        return response.json()
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Request timed out"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot connect to backend"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}

def upload_document(file_bytes, filename):
    """
    Upload document to backend.
    
    Args:
        file_bytes: PDF file content as bytes
        filename: Name of the file
        
    Returns:
        dict: Upload result
    """
    try:
        files = {"file": (filename, file_bytes, "application/pdf")}
        response = requests.post(f"{BACKEND_URL}/ingest", files=files, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Upload failed with status {response.status_code}: {response.text}"}
    except requests.exceptions.Timeout:
        return {"error": "Upload timed out after 120 seconds"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend"}
    except Exception as e:
        return {"error": f"Upload error: {str(e)}"}

def search_documents(query):
    """
    Search documents using semantic similarity.
    
    Args:
        query: Search query string
        
    Returns:
        dict: Search results
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/search",
            json={"query": query},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Log query to audit trail
            result_count = len(result.get("results", []))
            log_query_to_audit(
                user="frontend_user",  # Can be extended with actual user tracking
                query=query,
                result_count=result_count
            )
            
            return result
        else:
            return {"error": f"Search failed with status {response.status_code}: {response.text}"}
    except requests.exceptions.Timeout:
        return {"error": "Search timed out after 30 seconds"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend"}
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}

def start_triage(source_folder, target_relevant, target_irrelevant, criteria, max_pages, sampling_strategy="linear"):
    """
    Start triage process for batch file sorting.
    
    Args:
        source_folder: Path to source folder
        target_relevant: Path to relevant folder
        target_irrelevant: Path to irrelevant folder
        criteria: Classification criteria
        max_pages: Maximum pages to analyze per document
        sampling_strategy: Strategy for selecting pages - "linear" or "random"
        
    Returns:
        dict: Triage results with statistics and audit log
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/triage/batch",
            json={
                "source_folder": source_folder,
                "target_relevant": target_relevant,
                "target_irrelevant": target_irrelevant,
                "criteria": criteria,
                "max_pages": max_pages,
                "sampling_strategy": sampling_strategy
            },
            timeout=TRIAGE_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Triage failed with status {response.status_code}: {response.text}"}
    except requests.exceptions.Timeout:
        return {"error": f"Triage timed out after {TRIAGE_TIMEOUT} seconds"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend"}
    except Exception as e:
        return {"error": f"Triage error: {str(e)}"}

def main():
    """
    Main application function.
    
    Handles UI rendering, session state management, and user interactions.
    Wrapped in try/except for friendly error handling.
    """
    try:
        # Check for network connection on startup and display warning
        if 'network_checked' not in st.session_state:
            st.session_state.network_checked = True
            if check_network_connection():
                st.warning("⚠️ **Network connection detected.** For maximum security, disconnect from the internet before processing confidential documents.")
        
        # Initialize session state variables
        if 'language' not in st.session_state:
            st.session_state.language = 'sv'  # Default to Swedish
        
        if 'has_documents' not in st.session_state:
            st.session_state.has_documents = False
        
        # Language selector in sidebar
        st.sidebar.title("⚙️ Inställningar")
        language = st.sidebar.selectbox(
            "Language / Språk",
            options=["sv", "en"],
            format_func=lambda x: "Svenska" if x == "sv" else "English"
        )
        
        # Store language in session state
        if 'language' not in st.session_state or st.session_state.language != language:
            st.session_state.language = language
        
        # Get translations based on language
        t = get_translations(language)
        
        # Main title with cleaner presentation
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("🔐 Nordic Secure")
            st.caption(t["app_subtitle"])
        
        # Welcome message if no documents uploaded yet
        if not st.session_state.has_documents:
            st.info(t["welcome_message"])
        
        # Check license status
        with st.spinner(t["checking_license"]):
            license_status = check_license()
        
        # Display license status in sidebar
        st.sidebar.markdown("---")
        st.sidebar.subheader(t["license_status"])
        if license_status.get("valid"):
            st.sidebar.success(t["license_active"])
        else:
            st.sidebar.warning(t["license_expired"])
        
        # License activation section in sidebar
        with st.sidebar.expander(t["activate_license"]):
            with st.form("license_form"):
                license_key = st.text_input(t["license_key_label"], type="password")
                submitted = st.form_submit_button(t["activate_button"])
                
                if submitted and license_key:
                    with st.spinner(t["activating"]):
                        result = activate_license(license_key)
                        
                        if result.get("success"):
                            st.success(t["activation_success"])
                            st.rerun()
                        else:
                            st.error(f"{t['activation_failed']}: {result.get('message', 'Unknown error')}")
        
        # Create tabs with better spacing
        st.markdown("---")
        tab_chat, tab_upload, tab_triage = st.tabs([
            t["tab_chat"],
            t["tab_upload"],
            t["tab_triage"]
        ])
        
        # Tab 1: Chat/Search
        with tab_chat:
            st.header(t["chat_header"])
            st.write(t["chat_description"])
            
            # Use columns for better layout
            col1, col2 = st.columns([4, 1])
            with col1:
                query = st.text_input(
                    t["search_query_label"], 
                    placeholder=t["search_query_placeholder"],
                    label_visibility="collapsed"
                )
            with col2:
                search_clicked = st.button(t["search_button"], use_container_width=True)
            
            if search_clicked:
                if query:
                    with st.spinner(t["searching"]):
                        results = search_documents(query)
                        
                        if "error" in results:
                            st.error(f"{t['error']}: {results['error']}")
                        elif "results" in results and results["results"]:
                            st.success(f"{t['found_results']}: {len(results['results'])}")
                            
                            for i, result in enumerate(results["results"], 1):
                                with st.expander(f"📄 {t['result']} {i} - {result.get('metadata', {}).get('filename', 'Document')}"):
                                    col1, col2 = st.columns([1, 4])
                                    with col1:
                                        st.metric(t['similarity'], f"{result.get('distance', 'N/A')}")
                                    with col2:
                                        st.write(f"**{t['content']}:**")
                                        st.write(result.get("document", "")[:500] + "...")
                        else:
                            st.info(t["no_results"])
                else:
                    st.warning(t["enter_query"])
        
        # Tab 2: Upload
        with tab_upload:
            st.header(t["upload_header"])
            st.write(t["upload_description"])
            
            uploaded_file = st.file_uploader(
                t["choose_file"],
                type=["pdf"],
                help=t["upload_help"]
            )
            
            if uploaded_file is not None:
                # Display file info in columns
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{t['filename']}:** {uploaded_file.name}")
                with col2:
                    st.write(f"**{t['filesize']}:** {uploaded_file.size / 1024:.2f} KB")
                with col3:
                    upload_clicked = st.button(t["upload_button"], type="primary", use_container_width=True)
                
                if upload_clicked:
                    with st.spinner(t["uploading"]):
                        result = upload_document(uploaded_file.getvalue(), uploaded_file.name)
                        
                        if "error" in result:
                            st.error(f"{t['error']}: {result['error']}")
                        elif "document_id" in result:
                            st.success(t["upload_success"])
                            st.session_state.has_documents = True
                            st.info(f"📋 {t['document_id']}: {result['document_id']}")
                        else:
                            st.warning(t["upload_unknown"])
        
        # Tab 3: Mass Sorting / Triage
        with tab_triage:
            st.header(t["triage_title"])
            st.write(t["triage_description"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                source_folder = st.text_input(
                    t["source_folder"],
                    help=t["source_folder_help"],
                    placeholder="/path/to/inbox"
                )
                
                target_relevant = st.text_input(
                    t["target_relevant"],
                    help=t["target_relevant_help"],
                    placeholder="/path/to/relevant"
                )
            
            with col2:
                target_irrelevant = st.text_input(
                    t["target_irrelevant"],
                    help=t["target_irrelevant_help"],
                    placeholder="/path/to/irrelevant"
                )
                
                max_pages = st.number_input(
                    t["max_pages_label"],
                    min_value=1,
                    max_value=20,
                    value=5,
                    help=t["max_pages_help"]
                )
                
                sampling_strategy = st.selectbox(
                    t["sampling_strategy_label"],
                    options=["linear", "random"],
                    format_func=lambda x: t[f"sampling_{x}"],
                    help=t["sampling_strategy_help"]
                )
            
            criteria = st.text_area(
                t["sorting_criteria"],
                help=t["sorting_criteria_help"],
                placeholder=t["sorting_criteria_placeholder"],
                height=100
            )
            
            if st.button(t["start_sorting"], type="primary"):
                # Validate inputs
                if not source_folder or not target_relevant or not target_irrelevant:
                    st.error(t["error_missing_paths"])
                elif not criteria:
                    st.error(t["error_no_criteria"])
                else:
                    # Create progress indicators
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    log_expander = st.expander(t["live_log"], expanded=True)
                    log_container = log_expander.empty()
                    
                    # Start triage
                    with st.spinner(t["processing"]):
                        result = start_triage(
                            source_folder,
                            target_relevant,
                            target_irrelevant,
                            criteria,
                            max_pages,
                            sampling_strategy
                        )
                        
                        if "error" in result:
                            st.error(f"{t['error']}: {result['error']}")
                        elif "total_files" in result:
                            progress_bar.progress(100)
                            st.success(t["complete"])
                            
                            # Display statistics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(t["total_files"], result["total_files"])
                            with col2:
                                st.metric(t["relevant"], result["relevant"])
                            with col3:
                                st.metric(t["irrelevant"], result["irrelevant"])
                            with col4:
                                st.metric(t["errors"], result["errors"])
                            
                            # Display audit log
                            if "audit_log" in result and result["audit_log"]:
                                st.subheader(t["audit_log_title"])
                                
                                df = pd.DataFrame(result["audit_log"])
                                st.dataframe(df, use_container_width=True)
                                
                                # Download button for audit log
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label=t["download_log"],
                                    data=csv,
                                    file_name=f"triage_audit_log_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                        else:
                            st.warning(t["unknown_response"])
    
    except Exception as e:
        # Friendly error handling - no stack traces for users
        # Use fallback messages in case translations not loaded
        error_msg = "⚠️ Ett fel uppstod"
        restart_msg = "Försök starta om applikationen."
        
        # Try to use translations if available, but don't fail if not
        try:
            if 't' in locals():
                error_msg = t.get("error_occurred", error_msg)
                restart_msg = t.get("error_restart_message", restart_msg)
        except:
            pass  # Use fallback messages
        
        st.error(error_msg)
        st.info(restart_msg)
        
        # Log error for debugging (already imported at top)
        print(f"Error in main UI: {e}")
        print(traceback.format_exc())

def get_translations(language: str) -> dict:
    """Get translations for specified language"""
    translations = {
        "en": {
            # App
            "app_subtitle": "Secure Document Management for Legal Professionals",
            "welcome_message": "👋 Welcome to Nordic Secure. Upload documents to get started.",
            "checking_license": "Verifying license...",
            "error_occurred": "⚠️ An error occurred",
            "error_restart_message": "Please try restarting the application.",
            
            # License
            "license_status": "License Status",
            "license_active": "✅ Active License",
            "license_expired": "⚠️ License Required",
            "activate_license": "Activate License",
            "license_key_label": "License Key",
            "activate_button": "Activate",
            "activating": "Activating license...",
            "activation_success": "✅ License activated successfully!",
            "activation_failed": "❌ Activation failed",
            
            # Tabs
            "tab_chat": "💬 Search",
            "tab_upload": "📤 Upload",
            "tab_triage": "🗂️ Batch Sorting",
            
            # Chat tab
            "chat_header": "💬 Document Search",
            "chat_description": "Search through your documents using natural language.",
            "search_query_label": "Enter your search query",
            "search_query_placeholder": "e.g., What is the policy on data retention?",
            "search_button": "🔍 Search",
            "searching": "Searching documents...",
            "found_results": "Found results",
            "result": "Result",
            "similarity": "Relevance",
            "content": "Content",
            "no_results": "No results found.",
            "enter_query": "Please enter a search query.",
            "error": "Error",
            
            # Upload tab
            "upload_header": "📤 Upload Documents",
            "upload_description": "Add PDF documents to your secure archive.",
            "choose_file": "Choose a PDF file",
            "upload_help": "Only PDF files are supported",
            "filename": "Filename",
            "filesize": "File size",
            "document_id": "Document ID",
            "upload_button": "📤 Upload",
            "uploading": "Processing document...",
            "upload_success": "✅ Document uploaded successfully!",
            "upload_unknown": "Upload completed with unknown status.",
            
            # Triage tab
            "triage_title": "🗂️ AI-Powered Batch Sorting",
            "triage_description": "Automatically sort large volumes of documents based on your criteria.",
            "source_folder": "📁 Source Folder",
            "source_folder_help": "Path to the folder containing files to sort",
            "target_relevant": "✅ Target Folder: Relevant",
            "target_relevant_help": "Path where relevant files will be moved",
            "target_irrelevant": "❌ Target Folder: Other",
            "target_irrelevant_help": "Path where non-relevant files will be moved",
            "max_pages_label": "Max Pages to Analyze",
            "max_pages_help": "Limit analysis to first N pages (recommended: 3-5)",
            "sampling_strategy_label": "📄 Sampling Strategy",
            "sampling_strategy_help": "Choose how pages are selected for analysis",
            "sampling_linear": "Linear (First 5 pages)",
            "sampling_random": "Random (Start, Middle, End)",
            "sorting_criteria": "📋 Sorting Criteria",
            "sorting_criteria_help": "Describe what makes a document relevant",
            "sorting_criteria_placeholder": "E.g., Is this document related to a bankruptcy application?",
            "start_sorting": "🚀 Start Sorting",
            "processing": "Processing files...",
            "complete": "✅ Sorting Complete!",
            "live_log": "📋 Processing Log",
            "total_files": "Total Files",
            "relevant": "Relevant",
            "irrelevant": "Other",
            "errors": "Errors",
            "audit_log_title": "📊 Processing Report",
            "download_log": "⬇️ Download Report (CSV)",
            "error_missing_paths": "Please provide all folder paths.",
            "error_no_criteria": "Please provide sorting criteria.",
            "unknown_response": "Unknown response from server.",
        },
        "sv": {
            # App
            "app_subtitle": "Säker Dokumenthantering för Jurister och Revisorer",
            "welcome_message": "👋 Välkommen till Nordic Secure. Ladda upp dokument för att börja.",
            "checking_license": "Kontrollerar licens...",
            "error_occurred": "⚠️ Ett fel uppstod",
            "error_restart_message": "Försök starta om applikationen.",
            
            # License
            "license_status": "Licensstatus",
            "license_active": "✅ Aktiv Licens",
            "license_expired": "⚠️ Licens Krävs",
            "activate_license": "Aktivera Licens",
            "license_key_label": "Licensnyckel",
            "activate_button": "Aktivera",
            "activating": "Aktiverar licens...",
            "activation_success": "✅ Licensen är nu aktiv!",
            "activation_failed": "❌ Aktivering misslyckades",
            
            # Tabs
            "tab_chat": "💬 Sök",
            "tab_upload": "📤 Ladda upp",
            "tab_triage": "🗂️ Massbearbetning",
            
            # Chat tab
            "chat_header": "💬 Dokumentsökning",
            "chat_description": "Sök i dina dokument med naturligt språk.",
            "search_query_label": "Skriv din sökfråga",
            "search_query_placeholder": "t.ex. Vilka regler gäller för datalagring?",
            "search_button": "🔍 Sök",
            "searching": "Söker i dokument...",
            "found_results": "Hittade resultat",
            "result": "Resultat",
            "similarity": "Relevans",
            "content": "Innehåll",
            "no_results": "Inga resultat hittades.",
            "enter_query": "Vänligen ange en sökfråga.",
            "error": "Fel",
            
            # Upload tab
            "upload_header": "📤 Ladda upp Dokument",
            "upload_description": "Lägg till PDF-dokument i ditt säkra arkiv.",
            "choose_file": "Välj en PDF-fil",
            "upload_help": "Endast PDF-filer stöds",
            "filename": "Filnamn",
            "filesize": "Filstorlek",
            "document_id": "Dokument-ID",
            "upload_button": "📤 Ladda upp",
            "uploading": "Bearbetar dokument...",
            "upload_success": "✅ Dokumentet har laddats upp!",
            "upload_unknown": "Uppladdning slutförd med okänd status.",
            
            # Triage tab
            "triage_title": "🗂️ AI-Driven Massbearbetning",
            "triage_description": "Sortera automatiskt stora volymer dokument baserat på dina kriterier.",
            "source_folder": "📁 Källmapp",
            "source_folder_help": "Sökväg till mappen med filer som ska sorteras",
            "target_relevant": "✅ Målmapp: Träff",
            "target_relevant_help": "Sökväg dit relevanta filer kommer att flyttas",
            "target_irrelevant": "❌ Målmapp: Övrigt",
            "target_irrelevant_help": "Sökväg dit icke-relevanta filer kommer att flyttas",
            "max_pages_label": "Max Sidor att Analysera",
            "max_pages_help": "Begränsa analys till första N sidorna (rekommenderat: 3-5)",
            "sampling_strategy_label": "📄 Urvalsstrategi",
            "sampling_strategy_help": "Välj hur sidor väljs för analys",
            "sampling_linear": "Linjär (Första 5 sidorna)",
            "sampling_random": "Slumpmässig (Start, Mitten, Slut)",
            "sorting_criteria": "📋 Sorteringskriterier",
            "sorting_criteria_help": "Beskriv vad som gör ett dokument relevant",
            "sorting_criteria_placeholder": "T.ex. Är detta dokument relaterat till en konkursansökan?",
            "start_sorting": "🚀 Starta Bearbetning",
            "processing": "Bearbetar filer...",
            "complete": "✅ Bearbetning Klar!",
            "live_log": "📋 Bearbetningslogg",
            "total_files": "Totalt Filer",
            "relevant": "Träffar",
            "irrelevant": "Övrigt",
            "errors": "Fel",
            "audit_log_title": "📊 Bearbetningsrapport",
            "download_log": "⬇️ Ladda ner Rapport (CSV)",
            "error_missing_paths": "Vänligen ange alla mappsökvägar.",
            "error_no_criteria": "Vänligen ange sorteringskriterier.",
            "unknown_response": "Okänt svar från servern.",
        }
    }
    
    return translations.get(language, translations["en"])

if __name__ == "__main__":
    main()
