"""
PyInstaller runtime hook for Streamlit
Ensures Streamlit can find its configuration, data files, and package metadata in the PyInstaller bundle.

This hook fixes the error:
  importlib.metadata.PackageNotFoundError: No package metadata was found for streamlit

The issue occurs because PyInstaller bundles don't automatically configure the metadata
search paths that importlib.metadata uses to find .dist-info directories.
"""

import os
import sys
from pathlib import Path

# Configure metadata search path for PyInstaller bundle
if getattr(sys, '_MEIPASS', None):
    # Running in PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)
    bundle_dir_str = str(bundle_dir)
    
    # CRITICAL: Add bundle directory to sys.path so importlib.metadata can find
    # the .dist-info directories that were copied by copy_metadata() in the spec file.
    # importlib.metadata searches sys.path for .dist-info directories containing
    # package metadata (METADATA, RECORD files, etc.)
    if bundle_dir_str not in sys.path:
        sys.path.insert(0, bundle_dir_str)
    
    # Set Streamlit home directory
    streamlit_dir = bundle_dir / '.streamlit'
    if streamlit_dir.exists():
        os.environ['STREAMLIT_CONFIG_DIR'] = str(streamlit_dir)
    
    # Ensure Streamlit can find its static files
    os.environ['STREAMLIT_STATIC_DIR'] = str(bundle_dir)
