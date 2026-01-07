@echo off
REM ============================================================================
REM Nordic Secure - Licensgenerator Byggskript
REM Bygger admin_keygen.py till en fristående EXE-fil
REM ============================================================================

echo.
echo ============================================
echo Nordic Secure - Licensgenerator Byggskript
echo ============================================
echo.

REM Kontrollera att PyInstaller är installerat
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo FELMEDDELANDE: PyInstaller är inte installerat!
    echo.
    echo Installera det genom att köra:
    echo   pip install pyinstaller
    echo.
    pause
    exit /b 1
)

echo PyInstaller hittades - fortsätter med bygget...
echo.

REM Ta bort gamla build-artefakter
if exist "dist\admin_keygen.exe" (
    echo Tar bort gammal EXE-fil...
    del /f /q "dist\admin_keygen.exe"
)

if exist "build\admin_keygen" (
    echo Tar bort gammal build-mapp...
    rmdir /s /q "build\admin_keygen"
)

echo.
echo [1/2] Bygger admin_keygen.exe...
echo Detta kan ta någon minut...
echo.

REM Bygg med PyInstaller (onefile och console mode)
python -m PyInstaller --onefile --console admin_keygen.py

if errorlevel 1 (
    echo.
    echo FELMEDDELANDE: Bygget misslyckades!
    echo Kontrollera felmeddelanden ovan.
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Klart!
echo.

REM Kontrollera att filen skapades
if not exist "dist\admin_keygen.exe" (
    echo FELMEDDELANDE: dist\admin_keygen.exe hittades inte!
    echo Bygget kan ha misslyckats.
    echo.
    pause
    exit /b 1
)

echo ============================================
echo LYCKAT!
echo ============================================
echo.
echo EXE-filen finns nu här: dist\admin_keygen.exe
echo.
echo Dubbelklicka på filen för att generera licensnycklar!
echo.
echo OBS: Filen customer_db.csv kommer att skapas i samma
echo      mapp där du kör admin_keygen.exe
echo.
echo ============================================
echo.

pause
