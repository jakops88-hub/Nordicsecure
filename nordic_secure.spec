# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Nordic Secure - Golden Master Production Build
Builds a standalone Windows executable with all dependencies bundled.
Includes pandas, openpyxl, and all required services.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

block_cipher = None

# Collect all necessary data files
datas = []

# Include backend and frontend as data directories
datas += [('backend', 'backend')]
datas += [('frontend', 'frontend')]

# Include locales directory if it exists (for language support)
if os.path.exists('locales'):
    datas += [('locales', 'locales')]

# Include .streamlit configuration if it exists
if os.path.exists('.streamlit'):
    datas += [('.streamlit', '.streamlit')]

# Include sentence-transformers models cache (if exists)
# Users may need to download models first: sentence-transformers will do this on first run
try:
    datas += collect_data_files('sentence_transformers')
except Exception:
    pass

# Include ChromaDB data files
try:
    datas += collect_data_files('chromadb')
except Exception:
    pass

# Include Streamlit data files and metadata
try:
    datas += collect_data_files('streamlit')
except Exception:
    pass

# Copy package metadata for packages that use importlib.metadata at runtime
# This fixes "PackageNotFoundError: No package metadata was found for streamlit"
# which occurs because PyInstaller doesn't automatically bundle .dist-info directories
# that contain the metadata files needed by importlib.metadata.version() and similar functions
# 
# IMPORTANT: Use package names (with dashes, e.g., 'pydantic-core') not module names
# Package names are used by pip and stored in .dist-info directories
# 
# Core packages that definitely need metadata:
# - streamlit: Main UI framework (causes the error)
# - altair: Used by Streamlit for charts
# - click: Used by Streamlit CLI
# - tornado: Streamlit's web server
# - packaging: Used for version parsing
metadata_packages = [
    'streamlit',
    'altair',
    'click',
    'tornado',
    'packaging',
    # Add packages required by ChromaDB and OpenTelemetry
    'chromadb',
    'opentelemetry-api',
    'opentelemetry-sdk',
    'opentelemetry-exporter-otlp-proto-grpc',
    'grpcio',
    'pydantic',
    'pydantic-core',
    'protobuf',
    'rich',
    'watchdog',
    'fastapi',
    'uvicorn',
    'starlette',
    'anyio',
    'httpcore',
    'httpx',
    'numpy',
    'pandas',
    'pyarrow',
]

for package in metadata_packages:
    try:
        datas += copy_metadata(package)
    except Exception:
        pass

# Include Altair data files (used by Streamlit for charts)
try:
    datas += collect_data_files('altair')
except Exception:
    pass

# Include pandas data files
try:
    datas += collect_data_files('pandas')
except Exception:
    pass

# Include external binaries (Ollama and Tesseract)
# These should be added manually to the dist folder after build
# or included here if they exist
if os.path.exists('bin'):
    datas += [('bin', 'bin')]

# Collect all submodules for packages that use dynamic imports
# IMPORTANT: Use Python module names (with underscores, e.g., 'pydantic_core') not package names
# Module names are used in Python imports: import pydantic_core
hiddenimports = [
    # FastAPI and related
    'uvicorn',
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
    
    # Streamlit
    'streamlit',
    'streamlit.web',
    'streamlit.web.cli',
    'streamlit.runtime',
    'streamlit.runtime.scriptrunner',
    
    # ChromaDB
    'chromadb',
    'chromadb.config',
    'chromadb.api',
    'chromadb.api.models',
    'chromadb.db',
    'chromadb.db.impl',
    
    # Sentence transformers and torch
    'sentence_transformers',
    'torch',
    'torchvision',
    
    # PDF processing
    'PyPDF2',
    'pdf2image',
    'pytesseract',
    'PIL',
    'PIL._imaging',
    
    # Data processing - pandas and openpyxl (required for triage_service)
    'pandas',
    'pandas._libs',
    'pandas._libs.tslibs',
    'pandas.io',
    'pandas.io.formats',
    'pandas.io.excel',
    'openpyxl',
    'openpyxl.cell',
    'openpyxl.styles',
    'openpyxl.worksheet',
    
    # Altair (used by Streamlit for charts)
    'altair',
    'altair.vegalite',
    'altair.vegalite.v5',
    
    # PyArrow (used by pandas for parquet files)
    'pyarrow',
    'pyarrow.parquet',
    
    # Other dependencies
    'numpy',
    'numpy.core',
    'requests',
    'cryptography',
    'pydantic',
    'pydantic_core',
    
    # OpenTelemetry (required by ChromaDB)
    'opentelemetry',
    'opentelemetry.sdk',
    'opentelemetry.sdk.resources',
    'opentelemetry.sdk._logs',
    'opentelemetry.sdk._logs._internal',
    'opentelemetry.exporter.otlp.proto.grpc',
    'opentelemetry.exporter.otlp.proto.grpc.trace_exporter',
    'opentelemetry.exporter.otlp.proto.grpc.exporter',
    
    # Concurrent futures
    'concurrent',
    'concurrent.futures',
    'concurrent.futures.thread',
    'concurrent.futures.process',
    
    # gRPC
    'grpc',
    'grpc._channel',
    'grpc._cython',
    'grpc._cython.cygrpc',
    
    # Additional imports
    'importlib.metadata',
    'importlib.resources',
    'importlib.resources.abc',
    
    # Threading support
    'threading',
]

# Collect submodules for packages with plugins
try:
    hiddenimports += collect_submodules('chromadb')
except Exception:
    pass

try:
    hiddenimports += collect_submodules('uvicorn')
except Exception:
    pass

try:
    hiddenimports += collect_submodules('streamlit')
except Exception:
    pass

try:
    hiddenimports += collect_submodules('pandas')
except Exception:
    pass

try:
    hiddenimports += collect_submodules('altair')
except Exception:
    pass

# Analysis
a = Analysis(
    ['main_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[
        os.path.abspath('hook-streamlit.py'),
        os.path.abspath('hook-chromadb.py')
    ],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'scipy',
        'jupyter',
        'notebook',
        'IPython',
        'sphinx',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ (Python ZIP archive)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NordicSecure',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window for production (clean startup)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add your icon here: icon='icon.ico'
)

# COLLECT
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NordicSecure'
)
