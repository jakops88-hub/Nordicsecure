# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Nordic Secure
Builds a standalone Windows executable with all dependencies bundled.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary data files
datas = []

# Include backend and frontend as data directories
datas += [('backend', 'backend')]
datas += [('frontend', 'frontend')]

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

# Include Streamlit data files
try:
    datas += collect_data_files('streamlit')
except Exception:
    pass

# Include external binaries (Ollama and Tesseract)
# These should be added manually to the dist folder after build
# or included here if they exist
if os.path.exists('bin'):
    datas += [('bin', 'bin')]

# Collect all submodules for packages that use dynamic imports
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
    
    # Other dependencies
    'numpy',
    'numpy.core',
    'requests',
    'cryptography',
    'pydantic',
    'pydantic_core',
    
    # Multiprocessing support
    'multiprocessing',
    'multiprocessing.spawn',
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

# Analysis
a = Analysis(
    ['main_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython',
        'sphinx',
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
    console=True,  # Set to False for production to hide console window
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
