import streamlit as st
import requests
import os
import tempfile
import io
import pandas as pd
from datetime import datetime
from pathlib import Path

# Backend URL from environment variable or default
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="Nordic Secure RAG System", page_icon="🔐", layout="wide")

def check_license():
    """Check license status with backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/license/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"valid": False, "message": "Could not verify license"}
    except requests.exceptions.RequestException:
        return {"valid": False, "message": "Backend connection failed"}

def activate_license(license_key: str):
    """Activate a license key"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/license/activate",
            json={"license_key": license_key},
            timeout=5
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}

def upload_document(file_bytes, filename):
    """Upload document to backend"""
    try:
        files = {"file": (filename, file_bytes, "application/pdf")}
        response = requests.post(f"{BACKEND_URL}/ingest", files=files, timeout=120)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def search_documents(query):
    """Search documents"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/search",
            json={"query": query},
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def start_triage(source_folder, target_relevant, target_irrelevant, criteria, max_pages):
    """Start triage process"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/triage/batch",
            json={
                "source_folder": source_folder,
                "target_relevant": target_relevant,
                "target_irrelevant": target_irrelevant,
                "criteria": criteria,
                "max_pages": max_pages
            },
            timeout=3600  # 1 hour timeout for batch processing
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    # Language selector in sidebar
    st.sidebar.title("⚙️ Settings")
    language = st.sidebar.selectbox(
        "Language / Språk",
        options=["en", "sv"],
        format_func=lambda x: "English" if x == "en" else "Svenska"
    )
    
    # Store language in session state
    if 'language' not in st.session_state or st.session_state.language != language:
        st.session_state.language = language
    
    # Get translations based on language
    t = get_translations(language)
    
    st.title("🔐 Nordic Secure RAG System")
    
    # Check license status
    license_status = check_license()
    
    # Display license status in sidebar
    st.sidebar.header(t["license_status"])
    if license_status.get("valid"):
        st.sidebar.success(t["license_active"])
    else:
        st.sidebar.error(t["license_expired"])
    
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
    
    # Create tabs
    tab_chat, tab_upload, tab_triage = st.tabs([
        t["tab_chat"],
        t["tab_upload"],
        t["tab_triage"]
    ])
    
    # Tab 1: Chat/Search
    with tab_chat:
        st.header(t["chat_header"])
        st.write(t["chat_description"])
        
        query = st.text_input(t["search_query_label"], placeholder=t["search_query_placeholder"])
        
        if st.button(t["search_button"]):
            if query:
                with st.spinner(t["searching"]):
                    results = search_documents(query)
                    
                    if "error" in results:
                        st.error(f"{t['error']}: {results['error']}")
                    elif "results" in results and results["results"]:
                        st.success(f"{t['found_results']}: {len(results['results'])}")
                        
                        for i, result in enumerate(results["results"], 1):
                            with st.expander(f"📄 {t['result']} {i} - {result.get('metadata', {}).get('filename', 'Document')}"):
                                st.write(f"**{t['similarity']}:** {result.get('distance', 'N/A')}")
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
            st.write(f"**{t['filename']}:** {uploaded_file.name}")
            st.write(f"**{t['filesize']}:** {uploaded_file.size / 1024:.2f} KB")
            
            if st.button(t["upload_button"]):
                with st.spinner(t["uploading"]):
                    result = upload_document(uploaded_file.getvalue(), uploaded_file.name)
                    
                    if "error" in result:
                        st.error(f"{t['error']}: {result['error']}")
                    elif "document_id" in result:
                        st.success(f"{t['upload_success']} ID: {result['document_id']}")
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
                        max_pages
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
                                file_name=f"triage_audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.warning(t["unknown_response"])

def get_translations(language: str) -> dict:
    """Get translations for specified language"""
    translations = {
        "en": {
            # License
            "license_status": "License Status",
            "license_active": "✅ Active License",
            "license_expired": "🔒 License Expired",
            "activate_license": "Activate License",
            "license_key_label": "License Key",
            "activate_button": "Activate",
            "activating": "Activating license...",
            "activation_success": "✅ License activated successfully!",
            "activation_failed": "❌ Activation failed",
            
            # Tabs
            "tab_chat": "💬 Chat",
            "tab_upload": "📤 Upload",
            "tab_triage": "🗂️ Mass Sorting",
            
            # Chat tab
            "chat_header": "💬 Search Documents",
            "chat_description": "Search through your uploaded documents using natural language queries.",
            "search_query_label": "Enter your search query",
            "search_query_placeholder": "e.g., What is the policy on data retention?",
            "search_button": "🔍 Search",
            "searching": "Searching...",
            "found_results": "Found results",
            "result": "Result",
            "similarity": "Similarity",
            "content": "Content",
            "no_results": "No results found.",
            "enter_query": "Please enter a search query.",
            "error": "Error",
            
            # Upload tab
            "upload_header": "📤 Upload Documents",
            "upload_description": "Upload PDF documents to add them to your knowledge base.",
            "choose_file": "Choose a PDF file",
            "upload_help": "Only PDF files are supported",
            "filename": "Filename",
            "filesize": "File size",
            "upload_button": "📤 Upload Document",
            "uploading": "Uploading and processing...",
            "upload_success": "✅ Document uploaded successfully!",
            "upload_unknown": "Upload completed with unknown status.",
            
            # Triage tab
            "triage_title": "🗂️ AI Triage - Batch File Sorting",
            "triage_description": "Automatically sort hundreds of unstructured files (PDF/Images) based on your criteria.",
            "source_folder": "📁 Source Folder (Inbox)",
            "source_folder_help": "Path to the folder containing files to sort",
            "target_relevant": "✅ Target Folder: Relevant",
            "target_relevant_help": "Path where relevant files will be moved",
            "target_irrelevant": "❌ Target Folder: Irrelevant",
            "target_irrelevant_help": "Path where non-relevant files will be moved",
            "max_pages_label": "Max Pages to Analyze",
            "max_pages_help": "Limit OCR to first N pages to save time (recommended: 3-5)",
            "sorting_criteria": "📋 Sorting Criteria",
            "sorting_criteria_help": "Describe what makes a document relevant",
            "sorting_criteria_placeholder": "E.g., Is this document related to a bankruptcy application or promissory note?",
            "start_sorting": "🚀 Start Sorting",
            "processing": "Processing files...",
            "complete": "✅ Sorting Complete!",
            "live_log": "📋 Live Execution Log",
            "total_files": "Total Files",
            "relevant": "Relevant",
            "irrelevant": "Irrelevant",
            "errors": "Errors",
            "audit_log_title": "📊 Audit Log",
            "download_log": "⬇️ Download Audit Log (CSV)",
            "error_missing_paths": "Please provide all folder paths.",
            "error_no_criteria": "Please provide sorting criteria.",
            "unknown_response": "Unknown response from server.",
        },
        "sv": {
            # License
            "license_status": "Licensstatus",
            "license_active": "✅ Aktiv Licens",
            "license_expired": "🔒 Licens Utgången",
            "activate_license": "Aktivera Licens",
            "license_key_label": "Licensnyckel",
            "activate_button": "Aktivera",
            "activating": "Aktiverar licens...",
            "activation_success": "✅ Licens aktiverad!",
            "activation_failed": "❌ Aktivering misslyckades",
            
            # Tabs
            "tab_chat": "💬 Chatt",
            "tab_upload": "📤 Ladda upp",
            "tab_triage": "🗂️ Mass-sortering",
            
            # Chat tab
            "chat_header": "💬 Sök Dokument",
            "chat_description": "Sök genom dina uppladdade dokument med naturligt språk.",
            "search_query_label": "Ange din sökfråga",
            "search_query_placeholder": "t.ex. Vad är policyn för datalagring?",
            "search_button": "🔍 Sök",
            "searching": "Söker...",
            "found_results": "Hittade resultat",
            "result": "Resultat",
            "similarity": "Likhet",
            "content": "Innehåll",
            "no_results": "Inga resultat hittades.",
            "enter_query": "Vänligen ange en sökfråga.",
            "error": "Fel",
            
            # Upload tab
            "upload_header": "📤 Ladda upp Dokument",
            "upload_description": "Ladda upp PDF-dokument för att lägga till dem i din kunskapsbas.",
            "choose_file": "Välj en PDF-fil",
            "upload_help": "Endast PDF-filer stöds",
            "filename": "Filnamn",
            "filesize": "Filstorlek",
            "upload_button": "📤 Ladda upp Dokument",
            "uploading": "Laddar upp och bearbetar...",
            "upload_success": "✅ Dokument uppladdat!",
            "upload_unknown": "Uppladdning slutförd med okänd status.",
            
            # Triage tab
            "triage_title": "🗂️ AI Triage - Batch-sortering",
            "triage_description": "Sortera automatiskt hundratals ostrukturerade filer (PDF/Bilder) baserat på dina kriterier.",
            "source_folder": "📁 Källmapp (Inkorg)",
            "source_folder_help": "Sökväg till mappen som innehåller filer att sortera",
            "target_relevant": "✅ Målmapp: Träff",
            "target_relevant_help": "Sökväg dit relevanta filer kommer att flyttas",
            "target_irrelevant": "❌ Målmapp: Övrigt",
            "target_irrelevant_help": "Sökväg dit icke-relevanta filer kommer att flyttas",
            "max_pages_label": "Max Sidor att Analysera",
            "max_pages_help": "Begränsa OCR till första N sidorna för att spara tid (rekommenderat: 3-5)",
            "sorting_criteria": "📋 Sorteringskriterier",
            "sorting_criteria_help": "Beskriv vad som gör ett dokument relevant",
            "sorting_criteria_placeholder": "T.ex. Är detta dokument relaterat till en konkursansökan eller skuldebrev?",
            "start_sorting": "🚀 Starta Sortering",
            "processing": "Bearbetar filer...",
            "complete": "✅ Sortering Klar!",
            "live_log": "📋 Live Exekveringslogg",
            "total_files": "Totalt Filer",
            "relevant": "Relevanta",
            "irrelevant": "Irrelevanta",
            "errors": "Fel",
            "audit_log_title": "📊 Revisionslogg",
            "download_log": "⬇️ Ladda ner Revisionslogg (CSV)",
            "error_missing_paths": "Vänligen ange alla mappsökvägar.",
            "error_no_criteria": "Vänligen ange sorteringskriterier.",
            "unknown_response": "Okänt svar från servern.",
        }
    }
    
    return translations.get(language, translations["en"])

if __name__ == "__main__":
    main()
