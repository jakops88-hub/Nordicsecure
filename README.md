# Nordic Secure

**Local, Offline AI for Legal and Financial Sectors**

Nordic Secure is a secure document analysis platform designed for regulated industries requiring absolute data sovereignty. Built specifically for lawyers, bankruptcy administrators, and auditors, it enables comprehensive analysis of sensitive case files without cloud dependencies or data transmission risks.

## Project Overview

Nordic Secure addresses the critical need for AI-powered document analysis in environments where data confidentiality is paramount. By running entirely on local infrastructure, the system eliminates cloud-based risks while delivering enterprise-grade document intelligence capabilities.

**Value Proposition:**

- **Zero Cloud Dependency**: Complete air-gapped operation with no external API calls or internet requirements
- **Regulatory Compliance**: GDPR-compliant by design with complete data sovereignty
- **Enterprise Security**: All processing occurs on-premises using local vector databases and inference engines
- **Operational Efficiency**: Analyze thousands of pages in minutes with automated triage and classification

## Key Features

### Document Chat (Deep Dive)

Conversational interface for in-depth case file analysis powered by Llama 3.

- Query complex legal and financial documents using natural language
- Receive precise answers with full source citations (page and line numbers)
- Maintain audit trails for all queries and responses
- Support for scanned documents through integrated OCR
- Multi-document context awareness for comprehensive case analysis

### Batch Triage (Automated Classification)

High-volume document processing and automated categorization for case management.

- Process hundreds of documents simultaneously based on custom criteria
- Automated classification with configurable taxonomies
- Excel-based audit trail generation for compliance reporting
- Bulk processing with progress tracking and error handling
- Configurable sorting rules for case-specific requirements

### Multi-Language Support

Full user interface localization for international operations.

- Complete UI support for Swedish and English
- OCR support for Swedish language documents
- Extensible language framework for additional locales

## Security Architecture

Nordic Secure implements a defense-in-depth security model with multiple layers of protection:

### Local Vector Database

- **ChromaDB** for document embedding storage
- All vector operations performed locally
- No external database connections required
- Persistent storage in local file system

### Local Inference Engine

- **Ollama** with Llama 3 model for natural language processing
- Complete model execution on local hardware
- No telemetry or external model API calls
- Configurable model parameters for performance tuning

### GDPR Compliance by Design

- No data transmission to external services
- Complete user control over data storage and deletion
- Audit logging for all document operations
- Support for air-gapped network environments

## Installation & Usage

### For Users (Production Deployment)

Nordic Secure is distributed as a self-contained Windows executable requiring minimal system configuration.

**Hardware Requirements:**

- **Operating System**: Windows 10/11 (64-bit)
- **RAM**: 16GB minimum, 32GB recommended for large document sets
- **Storage**: 20GB free disk space for application and models
- **Processor**: Modern multi-core CPU (Intel i5/AMD Ryzen 5 or higher)

**Installation Steps:**

1. Run the `NordicSecure_Setup.exe` installer
2. Follow the installation wizard prompts
3. Launch Nordic Secure from the Start Menu or desktop shortcut
4. On first run, the application will initialize the local AI model (5-10 minutes)
5. Access the web interface at `http://localhost:8501`

**Initial Configuration:**

- Configure language preference (Swedish/English) in the settings panel
- Set default document storage location
- Configure triage classification rules if using batch processing

### For Developers (Development Environment)

**Prerequisites:**

- Python 3.10 or 3.11
- Git for version control
- 16GB RAM minimum for development and testing

**Environment Setup:**

1. Clone the repository:

```bash
git clone https://github.com/jakops88-hub/Nordicsecure.git
cd Nordicsecure
```

2. Install Python dependencies:

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

3. Configure the `bin/` directory structure:

```
Nordicsecure/
├── bin/
│   ├── ollama/
│   │   ├── ollama.exe          # Ollama runtime for Windows
│   │   └── models/             # Downloaded Llama 3 models
│   └── tesseract/
│       ├── tesseract.exe       # OCR engine
│       └── tessdata/
│           ├── eng.traineddata # English language data
│           └── swe.traineddata # Swedish language data
```

4. Download required binaries:

**Ollama:**
- Download from: https://ollama.ai/download/windows
- Place `ollama.exe` in `bin/ollama/`
- Pull Llama 3 model: `ollama pull llama3`

**Tesseract OCR:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Extract to `bin/tesseract/`
- Ensure language data files are in `bin/tesseract/tessdata/`

5. Run the application:

```bash
python main_launcher.py
```

6. Access the application at `http://localhost:8501`

**Development Commands:**

```bash
# Run backend tests
python -m pytest backend/

# Run with debug logging
python main_launcher.py --debug

# Build production executable
python -m PyInstaller nordic_secure.spec
```

**Project Structure:**

```
Nordicsecure/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── document_service.py  # Document processing and search
│   │   │   ├── triage_service.py    # Batch classification
│   │   │   └── language_service.py  # Localization support
│   │   ├── config/
│   │   │   └── config.py            # Application configuration
│   │   └── license_manager.py       # License verification
│   ├── main.py                      # FastAPI application entry point
│   └── requirements.txt             # Backend dependencies
├── frontend/
│   ├── app.py                       # Streamlit web interface
│   └── requirements.txt             # Frontend dependencies
├── bin/                             # External binaries (Ollama, Tesseract)
├── main_launcher.py                 # Main application launcher
├── nordic_secure.spec               # PyInstaller build specification
└── README.md
```

## Technology Stack

- **Backend Framework**: FastAPI (Python)
- **Frontend Framework**: Streamlit (Python)
- **Vector Database**: ChromaDB
- **AI/ML Engine**: Ollama with Llama 3
- **OCR Engine**: Tesseract with multi-language support
- **Document Processing**: PyPDF2, pdf2image
- **Data Export**: Pandas, openpyxl (Excel generation)

## License

**Proprietary / Closed Source**

This software is proprietary and confidential. Unauthorized copying, distribution, or use of this software, via any medium, is strictly prohibited without express written permission from the copyright holder.

For licensing inquiries, please contact the development team.
