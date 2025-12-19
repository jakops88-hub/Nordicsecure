# ============================================
# Stage 1: Builder - Compile Python to Binary
# ============================================
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-swe \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements and install all dependencies including PyInstaller
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyinstaller==6.3.0

# Copy application source code
COPY . .

# Create PyInstaller spec file with proper hidden imports
RUN cat > main.spec <<EOF
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['/build'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pgvector',
        'pgvector.sqlalchemy',
        'pypdf',
        'pypdf._reader',
        'passlib.handlers',
        'passlib.handlers.bcrypt',
        'sqlalchemy.sql.default_comparator',
        'pydantic',
        'pydantic.deprecated',
        'pydantic.deprecated.decorator',
        'pytesseract',
        'pdf2image',
        'PIL',
        'PIL._imaging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='nordicsecure',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

# Build the binary executable
RUN pyinstaller --clean --onefile main.spec

# Verify the binary was created
RUN ls -lh /build/dist/nordicsecure

# ============================================
# Stage 2: Final - Runtime Image
# ============================================
FROM python:3.10-slim

# Install ONLY runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-swe \
    poppler-utils \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy ONLY the compiled binary from builder stage
COPY --from=builder /build/dist/nordicsecure /app/nordicsecure

# Make binary executable
RUN chmod +x /app/nordicsecure

# Verify no Python source files are present
RUN echo "Verifying no .py files in image..." && \
    (find /app -name "*.py" | grep -q . && echo "ERROR: Python source files found!" && exit 1 || echo "SUCCESS: No .py files found")

# Expose port
EXPOSE 8000

# Run the binary
CMD ["/app/nordicsecure", "--host", "0.0.0.0", "--port", "8000"]
