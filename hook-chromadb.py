"""
PyInstaller runtime hook for ChromaDB
Disables telemetry before ChromaDB imports to prevent atexit registration errors.
"""

import os

# CRITICAL: Disable telemetry BEFORE importing any other packages
# This prevents ChromaDB/OpenTelemetry from registering atexit handlers
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"
