"""
PyInstaller runtime hook for Streamlit
Ensures Streamlit can find its configuration and data files in the PyInstaller bundle.
"""

import os
import sys
from pathlib import Path

# Set Streamlit config directory
if getattr(sys, '_MEIPASS', None):
    # Running in PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)
    
    # Set Streamlit home directory
    streamlit_dir = bundle_dir / '.streamlit'
    if streamlit_dir.exists():
        os.environ['STREAMLIT_CONFIG_DIR'] = str(streamlit_dir)
    
    # Ensure Streamlit can find its static files
    os.environ['STREAMLIT_STATIC_DIR'] = str(bundle_dir)
