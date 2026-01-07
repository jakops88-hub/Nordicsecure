"""
PyInstaller runtime hook for ChromaDB
Disables telemetry before ChromaDB imports to prevent atexit registration errors.

This is part of a defense-in-depth strategy:
1. hook-chromadb.py (this file) - Runs earliest, before PyInstaller bundle loads
2. main_launcher.py - Sets env vars immediately after os/sys imports
3. backend/database.py - Sets env vars with setdefault before chromadb import

Multiple layers ensure telemetry is disabled regardless of import order.
"""

import os

# CRITICAL: Disable telemetry BEFORE importing any other packages
# This prevents ChromaDB/OpenTelemetry from registering atexit handlers
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"
