# Nordic Secure - Build Guide for Windows Native Deployment

This guide explains how to build Nordic Secure as a native Windows application that requires no Docker, Python, or PostgreSQL installation from the end user.

## Overview

The final application will be:
- **Zero-config**: One-click installation with no prerequisites
- **Portable**: All dependencies bundled, data stored locally
- **Self-contained**: Includes Ollama, Tesseract OCR, and all Python dependencies
- **Native**: Runs as a standard Windows application

## Prerequisites for Building

### Required Software
1. **Python 3.10 or 3.11** (for building only)
2. **PyInstaller** (`pip install pyinstaller`)
3. **Inno Setup 6** (for creating the installer)
4. **Visual Studio Build Tools** (for some Python packages)

### Required External Binaries

You need to download and prepare these binaries before building:

#### 1. Ollama for Windows
- Download from: https://ollama.ai/download/windows
- Extract `ollama.exe`
- Place in: `bin/ollama.exe`

#### 2. Tesseract OCR (Portable)
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Get the portable version or extract from installer
- Create directory structure:
  ```
  bin/
    tesseract/
      tesseract.exe
      tessdata/
        eng.traineddata
        swe.traineddata (optional, for Swedish)
        ... (other language files as needed)
  ```

## Project Structure

Before building, your project should have this structure:

```
Nordicsecure/
├── main_launcher.py          # Main entry point
├── backend/
│   ├── main.py               # FastAPI application
│   ├── database.py           # ChromaDB integration
│   ├── requirements.txt      # Python dependencies
│   └── app/
│       └── services/
│           └── document_service.py
├── frontend/
│   ├── app.py                # Streamlit application
│   └── requirements.txt      # Streamlit dependencies
├── bin/                      # External binaries (NOT in git)
│   ├── ollama.exe
│   └── tesseract/
│       ├── tesseract.exe
│       └── tessdata/
│           ├── eng.traineddata
│           └── ...
├── nordic_secure.spec        # PyInstaller specification
└── setup.iss                 # Inno Setup script
```

## Building Process

### Step 1: Prepare Environment

1. **Create a clean virtual environment:**
   ```bash
   python -m venv venv_build
   venv_build\Scripts\activate
   ```

2. **Install all dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   pip install pyinstaller
   ```

3. **Download and place external binaries:**
   - Place `ollama.exe` in `bin/`
   - Place Tesseract in `bin/tesseract/`

### Step 2: Build with PyInstaller

Run PyInstaller with the spec file:

```bash
pyinstaller nordic_secure.spec
```

This will:
- Compile `main_launcher.py` and all Python code
- Bundle all dependencies (ChromaDB, FastAPI, Streamlit, etc.)
- Include `backend/` and `frontend/` folders as data
- Create executable in `dist/NordicSecure/`

**Note:** The first build may take 10-20 minutes as it downloads and compiles dependencies.

### Step 3: Test the Build

Before creating the installer, test the build:

```bash
cd dist\NordicSecure
NordicSecure.exe
```

Verify:
- All three services start (Ollama, Backend, Frontend)
- Frontend opens in browser at http://127.0.0.1:8501
- You can upload and search documents
- Data persists after restart (in `%APPDATA%\NordicSecure\data\`)

### Step 4: Create Installer with Inno Setup

1. **Copy external binaries to dist:**
   ```bash
   xcopy /E /I bin dist\NordicSecure\bin
   ```

2. **Open Inno Setup Compiler**
3. **Load** `setup.iss`
4. **Build** → Compile

This creates `NordicSecureSetup.exe` in the `Output/` directory.

### Step 5: Test the Installer

1. Run `NordicSecureSetup.exe` on a clean Windows machine (or VM)
2. Follow installation wizard
3. Launch from desktop shortcut
4. Verify all functionality

## Path Resolution Strategy

The application uses smart path resolution to work in all scenarios:

### Data Storage
- **Development:** `./data/chroma_db/` (project directory)
- **Production:** `%APPDATA%\NordicSecure\data\chroma_db\` (user directory)

### External Binaries
- Uses `sys._MEIPASS` to find bundled resources
- Falls back to relative paths for development

### Tesseract OCR
- Configured in `document_service.py`
- Points to `./bin/tesseract/tesseract.exe` in bundle
- Falls back to system PATH if not found

## Troubleshooting

### Build Issues

**ImportError: No module named 'X'**
- Add the module to `hiddenimports` in `nordic_secure.spec`

**Missing DLL errors**
- Install Visual C++ Redistributable
- Check that all binary dependencies are included

**Large executable size**
- Normal for this type of application (500MB-1GB+)
- Includes PyTorch, ChromaDB, and all ML models

### Runtime Issues

**Ollama fails to start**
- Check that `bin/ollama.exe` exists and has correct permissions
- Check antivirus isn't blocking execution
- Check that port 11434 is available

**Tesseract OCR not working**
- Verify `bin/tesseract/tesseract.exe` exists
- Verify `tessdata/` folder contains `.traineddata` files
- Check logs for path resolution

**Data not persisting**
- Check `%APPDATA%\NordicSecure\data\` exists and is writable
- Verify user has permissions to write to AppData

## Distribution

### What to Include
- `NordicSecureSetup.exe` (installer)
- `README.txt` (user instructions)
- `LICENSE.txt` (if applicable)

### System Requirements (for end users)
- **OS:** Windows 10 or Windows 11 (64-bit)
- **RAM:** 8GB minimum, 16GB recommended (for ML models)
- **Disk:** 5GB free space
- **Dependencies:** None (all bundled)

### Installation Notes for End Users
1. Run `NordicSecureSetup.exe`
2. Follow installation wizard
3. Launch from desktop shortcut
4. Application will start automatically
5. Browser opens to http://127.0.0.1:8501

## Updates and Maintenance

### Updating the Application
1. Build new version with updated code
2. Increment version number in `setup.iss`
3. Create new installer
4. Distribute to users

### Data Migration
- User data is stored in `%APPDATA%\NordicSecure\data\`
- Data persists across application updates
- To backup: Copy the `data/` folder
- To restore: Paste into new installation's data folder

## Security Considerations

### Code Signing (Recommended)
- Sign `NordicSecure.exe` with a code signing certificate
- Sign `NordicSecureSetup.exe` with the same certificate
- Prevents "Unknown Publisher" warnings

### Antivirus False Positives
- PyInstaller executables may trigger false positives
- Submit to antivirus vendors for whitelisting
- Code signing helps reduce false positives

## License Considerations

Ensure compliance with licenses for:
- Ollama (MIT License)
- Tesseract OCR (Apache 2.0)
- Python packages (various - check each)
- Your own code license

## Support

For issues during build process:
1. Check all dependencies are installed
2. Verify external binaries are in place
3. Check PyInstaller and Inno Setup logs
4. Ensure clean build environment (fresh venv)

---

**Version:** 1.0  
**Last Updated:** 2025-12-22  
**Author:** Nordic Secure Development Team
