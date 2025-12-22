# Nordic Secure - Golden Master Build Guide

## Overview

This guide explains how to build the **Golden Master** production version of Nordic Secure as a standalone Windows executable using PyInstaller.

## What's Included

The Golden Master build includes:
- ✅ **Backend (FastAPI)**: Full API with document service, triage service, and ChromaDB
- ✅ **Frontend (Streamlit)**: User interface with multi-language support (EN/SV)
- ✅ **Triage Service**: Mass file sorting with pandas and openpyxl (Excel export)
- ✅ **Language Service**: English and Swedish translations
- ✅ **Process Manager**: Orchestrates Backend and Frontend services
- ✅ **Error Logging**: debug.log file for troubleshooting customer issues

## Build Process

### Prerequisites

Before building, ensure you have:
1. **Python 3.10 or 3.11** installed
2. **PyInstaller**: `pip install pyinstaller`
3. **All dependencies**: 
   ```bash
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```

### Quick Build (Windows)

Simply double-click on:
```
build_release.bat
```

This will:
1. Clean old build artifacts (build/ and dist/ directories)
2. Run PyInstaller with the spec file
3. Create the executable in `dist/NordicSecure/`

**Note**: First build may take 10-20 minutes.

### Manual Build

If you prefer to build manually:

```bash
# Clean old artifacts
rmdir /s /q build dist

# Run PyInstaller
python -m PyInstaller nordic_secure.spec
```

## Build Output

After successful build, you'll find:
- **Executable**: `dist/NordicSecure/NordicSecure.exe`
- **Dependencies**: All Python packages bundled inside
- **Data files**: backend/, frontend/, locales/ (if exists), .streamlit/ (if exists)

## Key Features of the Build

### 1. Process Manager (main_launcher.py)
- Entry point for the application
- Sets `IsWindowsApp="True"` environment variable
- Starts Backend (FastAPI) using `uvicorn.run()` in a thread
- Starts Frontend (Streamlit) using `streamlit.web.cli.main()` in main thread
- Comprehensive error logging to `debug.log`
- Proper `sys._MEIPASS` path handling for PyInstaller bundles

### 2. PyInstaller Configuration (nordic_secure.spec)
- **Hidden imports**: All required packages including:
  - pandas, openpyxl (for triage service Excel export)
  - chromadb (vector database)
  - uvicorn, streamlit (web frameworks)
  - altair, pyarrow (for charts and data processing)
- **Data files**: Includes backend/, frontend/, locales/, .streamlit/
- **Runtime hook**: Custom Streamlit hook for configuration

### 3. Streamlit Runtime Hook (hook-streamlit.py)
- Ensures Streamlit can find its configuration in PyInstaller bundle
- Sets proper environment variables for bundled execution

## Testing the Build

After building, test the executable:

```bash
cd dist\NordicSecure
NordicSecure.exe
```

**Expected behavior:**
1. Console window opens (debug mode)
2. Backend starts on http://127.0.0.1:8000
3. Frontend starts on http://127.0.0.1:8501
4. Browser opens automatically to Streamlit interface
5. `debug.log` file created in same directory

## Troubleshooting

### Build Errors

**"PyInstaller not found"**
```bash
pip install pyinstaller
```

**"Module not found during build"**
- Check that all dependencies are installed
- Module may need to be added to `hiddenimports` in `nordic_secure.spec`

**"Build takes too long / hangs"**
- First build is slow (downloads and compiles dependencies)
- Subsequent builds are much faster
- Allow 10-20 minutes for first build

### Runtime Errors

All runtime errors are logged to **debug.log** in the same directory as the executable.

**Backend fails to start**
- Check `debug.log` for error details
- Ensure port 8000 is available
- Check that backend/ directory is included in bundle

**Frontend fails to start**
- Check `debug.log` for error details  
- Ensure port 8501 is available
- Check that frontend/ directory is included in bundle

**"Import Error" for pandas/openpyxl**
- These are now included in hidden imports
- Rebuild with updated spec file

## File Structure

```
Nordicsecure/
├── main_launcher.py          # Process Manager (entry point)
├── nordic_secure.spec        # PyInstaller configuration
├── build_release.bat         # Build script (double-click to build)
├── hook-streamlit.py         # Streamlit runtime hook
├── backend/                  # FastAPI backend
│   ├── main.py
│   ├── app/
│   │   └── services/
│   │       ├── document_service.py
│   │       ├── triage_service.py    # Uses pandas & openpyxl
│   │       └── language_service.py  # Multi-language support
│   └── requirements.txt
├── frontend/                 # Streamlit frontend
│   ├── app.py
│   └── requirements.txt
└── locales/                  # Language files (if exists)
```

## Environment Variables

The Process Manager sets:
- `IsWindowsApp="True"` - Indicates running as .exe
- `BACKEND_URL="http://127.0.0.1:8000"` - Backend API URL

## Next Steps After Build

1. **Test locally**: Run the executable and verify all features work
2. **Copy external binaries** (if needed):
   - `bin/ollama.exe` (if using Ollama)
   - `bin/tesseract/` (if using OCR)
3. **Create installer**: Use Inno Setup with `setup.iss`
4. **Distribute**: Package the installer for deployment

## Production Considerations

### For Production Release:
1. Change console mode in `nordic_secure.spec`:
   ```python
   console=False,  # Hide console window
   ```
2. Add application icon:
   ```python
   icon='icon.ico',
   ```
3. Sign the executable with code signing certificate
4. Test on clean Windows machine

### System Requirements (End Users):
- Windows 10 or Windows 11 (64-bit)
- 8GB RAM minimum (16GB recommended for ML models)
- 5GB free disk space
- No Python, Docker, or other dependencies needed!

## Support

For build issues, check:
1. `debug.log` file for runtime errors
2. PyInstaller output for build errors
3. Ensure all dependencies are installed
4. Verify Python version is 3.10 or 3.11

---

**Build Date**: 2025-12-22  
**Version**: Golden Master  
**Status**: READY FOR PRODUCTION
