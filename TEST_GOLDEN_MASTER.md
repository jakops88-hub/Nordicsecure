# Testing Golden Master Build

## Overview
This document provides instructions for testing the Golden Master build implementation.

## Prerequisites

Before testing, ensure you have:

1. **Python Environment**
   ```bash
   python --version  # Should be 3.10 or 3.11
   ```

2. **Dependencies Installed**
   ```bash
   pip install pyinstaller
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```

3. **Ollama Binary** (REQUIRED)
   ```
   Project Structure:
   Nordicsecure/
   ├── bin/
   │   ├── ollama.exe          # Ollama executable
   │   └── models/             # Llama 3 model files
   │       └── [model files]
   ```

## Test 1: Syntax Validation ✅

```bash
cd /path/to/Nordicsecure
python -m py_compile main_launcher.py
```

**Expected**: No errors

**Status**: ✅ PASSED

## Test 2: Script Execution (Without Build)

```bash
cd /path/to/Nordicsecure
python main_launcher.py
```

**Expected Behavior**:
1. Log message: "Nordic Secure launcher starting..."
2. Log message: "Running as script. Base path: ..."
3. Step 1: Attempts to start Ollama
   - If `bin/ollama.exe` exists: Starts Ollama server
   - If missing: Warning logged to `startup_error.log`, continues without Ollama
4. Step 2: Starts Backend on port 8000
5. Step 3: Starts Frontend on port 8501
6. Browser opens to http://localhost:8501

**Log Files Created**:
- `debug.log` - General application logs
- `startup_error.log` - Startup errors (if Ollama missing)

**To Stop**: Press Ctrl+C (cleans up Ollama process automatically)

## Test 3: PyInstaller Build

```bash
cd /path/to/Nordicsecure
build_release.bat
```

**Expected Output**:
```
============================================================================
Nordic Secure - Golden Master Build
============================================================================

[1/4] Cleaning old build artifacts...
Removing old build directory...
Removing old dist directory...
Old artifacts cleaned.

[2/4] Running PyInstaller...
This may take 10-20 minutes on first build...
[PyInstaller output...]

[3/4] Build completed successfully!

[4/4] Build artifacts created in: dist\NordicSecure\

============================================================================
Build Summary:
============================================================================
- Executable: dist\NordicSecure\NordicSecure.exe
- Dependencies: All Python packages bundled
- Data files: backend/, frontend/, locales/, .streamlit/

NEXT STEPS:
1. Test the build: cd dist\NordicSecure && NordicSecure.exe
2. Copy external binaries (if needed):
   - bin\ollama.exe
   - bin\tesseract\
3. Create installer with Inno Setup (setup.iss)

============================================================================
Build completed successfully!
============================================================================
```

**Verify Build Output**:
```bash
dir dist\NordicSecure
```

Should contain:
- `NordicSecure.exe` - Main executable
- `backend/` - Backend service files
- `frontend/` - Frontend files
- `bin/` - Ollama and models (if present in source)
- Various DLL and support files

## Test 4: Built Executable

```bash
cd dist\NordicSecure
NordicSecure.exe
```

**Expected Behavior**:
1. Console window opens (if `console=True` in spec)
2. Logs show initialization messages
3. Ollama starts (or warning if missing)
4. Backend starts on http://127.0.0.1:8000
5. Frontend starts on http://127.0.0.1:8501
6. Browser opens automatically

**Verify in Browser**:
1. Navigate to http://localhost:8501
2. Should see Nordic Secure interface
3. Try uploading a document
4. Try searching

## Test 5: Error Handling

### Test 5a: Missing Ollama

1. Rename or remove `bin/ollama.exe` temporarily
2. Run `NordicSecure.exe`

**Expected**:
- Warning logged to console: "Ollama executable not found"
- Entry in `startup_error.log`:
  ```
  ============================================================
  Startup Error - [timestamp]
  ============================================================
  Ollama executable not found at: [path]
  ```
- Application continues and starts Backend/Frontend
- Browser opens (some features may not work)

### Test 5b: Port Already in Use

1. Start another service on port 8000 or 8501
2. Run `NordicSecure.exe`

**Expected**:
- Error logged to `debug.log`
- Application fails to start completely
- Error visible in console

### Test 5c: Graceful Shutdown

1. Start `NordicSecure.exe`
2. Wait for all services to start
3. Close the browser window
4. Press Ctrl+C in console

**Expected**:
- Log message: "Shutting down..."
- Log message: "Cleaning up processes..."
- Log message: "Terminating Ollama process (PID: ...)"
- Log message: "Ollama process terminated gracefully"
- Log message: "Cleanup complete"
- Application exits cleanly
- No background processes remain

**Verify No Processes**:
```bash
tasklist | findstr ollama
tasklist | findstr python
```
Should return empty (no lingering processes)

## Test 6: Log Files

### Check debug.log

```bash
type debug.log
```

**Should contain**:
- Timestamp for each log entry
- "Nordic Secure launcher starting..."
- "Running as PyInstaller bundle" (for .exe)
- "Starting Ollama server..."
- "Ollama process started with PID: ..."
- "Starting Backend (FastAPI) in thread..."
- "Starting Frontend (Streamlit) in main thread..."

### Check startup_error.log

```bash
type startup_error.log
```

**Should contain** (if Ollama was missing):
```
============================================================
Startup Error - 2025-12-22 08:11:30
============================================================
Ollama executable not found at: [path]
```

## Test 7: Stress Test

1. Start and stop the application 5 times
2. Check Task Manager for memory leaks
3. Verify no orphaned processes

**Expected**:
- Each startup is clean
- Each shutdown is complete
- No memory leaks
- No orphaned ollama.exe processes

## Test 8: Integration Test (Full Stack)

If you have Ollama and models set up:

1. Start `NordicSecure.exe`
2. Wait for all services to start
3. Upload a PDF document via the web interface
4. Perform a search query
5. Verify results are returned
6. Close application gracefully

**Expected**:
- All services communicate correctly
- Documents are processed
- Search returns results
- No errors in logs

## Troubleshooting

### Build Fails

**Symptom**: PyInstaller reports errors

**Check**:
1. All dependencies installed: `pip list`
2. Python version correct: `python --version`
3. PyInstaller version: `pip show pyinstaller`

**Solution**:
```bash
pip install --upgrade pyinstaller
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### Executable Crashes on Start

**Symptom**: .exe starts then immediately crashes

**Check**:
1. `debug.log` for error messages
2. `startup_error.log` for startup errors
3. Console output (if visible)

**Common Issues**:
- Missing dependencies: Check hiddenimports in `nordic_secure.spec`
- Path issues: Verify base_dir is correct
- Port conflicts: Check ports 8000 and 8501 are free

### Ollama Won't Start

**Symptom**: "Ollama executable not found" in logs

**Check**:
1. `bin/ollama.exe` exists in correct location
2. `bin/models/` directory exists with model files
3. File permissions are correct

**Solution**:
```bash
# Copy Ollama to correct location
xcopy /E /I path\to\ollama.exe dist\NordicSecure\bin\
xcopy /E /I path\to\models\* dist\NordicSecure\bin\models\
```

### Services Won't Stop

**Symptom**: Ctrl+C doesn't stop application

**Check**:
1. Task Manager for running processes
2. `debug.log` for cleanup messages

**Solution**:
```bash
# Force kill all processes
taskkill /F /IM NordicSecure.exe
taskkill /F /IM ollama.exe
```

## Success Criteria

The Golden Master build is successful if:

- ✅ `build_release.bat` completes without errors
- ✅ `NordicSecure.exe` is created in `dist\NordicSecure\`
- ✅ Executable starts and shows startup logs
- ✅ Ollama starts (if binary present) or logs warning (if missing)
- ✅ Backend starts on port 8000
- ✅ Frontend starts on port 8501 and opens browser
- ✅ Web interface is accessible and functional
- ✅ Application shuts down cleanly on Ctrl+C
- ✅ No orphaned processes remain after shutdown
- ✅ `debug.log` contains complete startup/shutdown logs
- ✅ `startup_error.log` logs any Ollama issues

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| Syntax Validation | ✅ PASSED | No errors |
| Script Execution | ⏳ PENDING | Requires bin/ollama.exe |
| PyInstaller Build | ⏳ PENDING | Requires full env setup |
| Built Executable | ⏳ PENDING | Requires build completion |
| Error Handling | ⏳ PENDING | Requires runtime testing |
| Log Files | ⏳ PENDING | Requires execution |
| Stress Test | ⏳ PENDING | Requires runtime testing |
| Integration Test | ⏳ PENDING | Requires Ollama + models |

## Next Steps

1. **User Action Required**: Set up `bin/ollama.exe` and `bin/models/`
2. Run `build_release.bat`
3. Execute tests 2-8 from this document
4. Report any issues found
5. Create installer with Inno Setup once all tests pass

---

**Test Plan Version**: 1.0  
**Last Updated**: 2025-12-22  
**Status**: READY FOR USER TESTING
