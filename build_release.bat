@echo off
REM ============================================================================
REM Nordic Secure - Build Release Script
REM Golden Master Production Build
REM ============================================================================

echo.
echo ============================================================================
echo Nordic Secure - Golden Master Build
echo ============================================================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed!
    echo Please run: pip install pyinstaller
    echo.
    pause
    exit /b 1
)

echo [1/4] Cleaning old build artifacts...
echo.

REM Remove old build directories
if exist "build" (
    echo Removing old build directory...
    rmdir /s /q "build"
)

if exist "dist" (
    echo Removing old dist directory...
    rmdir /s /q "dist"
)

echo Old artifacts cleaned.
echo.

echo [2/4] Running PyInstaller...
echo This may take 10-20 minutes on first build...
echo.

REM Run PyInstaller with the spec file
python -m PyInstaller nordic_secure.spec

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    echo Check the output above for error messages.
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] Build completed successfully!
echo.

REM Check if dist directory was created
if not exist "dist\NordicSecure" (
    echo ERROR: dist\NordicSecure directory not found!
    echo Build may have failed.
    echo.
    pause
    exit /b 1
)

echo [4/4] Build artifacts created in: dist\NordicSecure\
echo.
echo ============================================================================
echo Build Summary:
echo ============================================================================
echo - Executable: dist\NordicSecure\NordicSecure.exe
echo - Dependencies: All Python packages bundled
echo - Data files: backend/, frontend/, locales/, .streamlit/
echo.
echo NEXT STEPS:
echo 1. Test the build: cd dist\NordicSecure && NordicSecure.exe
echo 2. Copy external binaries (if needed):
echo    - bin\ollama.exe
echo    - bin\tesseract\
echo 3. Create installer with Inno Setup (setup.iss)
echo.
echo ============================================================================
echo Build completed successfully!
echo ============================================================================
echo.

pause
