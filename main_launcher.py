#!/usr/bin/env python
"""
Nordic Secure Main Launcher - Process Manager
Entry point for the Golden Master production build.
Manages Ollama, Backend (FastAPI) and Frontend (Streamlit) services.
"""

import os
import sys

# CRITICAL: Disable telemetry BEFORE importing any other packages
# This prevents ChromaDB/OpenTelemetry from registering atexit handlers
# 
# Defense-in-depth strategy (multiple layers):
# 1. hook-chromadb.py - Runs earliest, before PyInstaller bundle loads
# 2. main_launcher.py (here) - Sets env vars immediately after os/sys imports
# 3. backend/database.py - Uses setdefault before chromadb import
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"

import threading
import time
import logging
import subprocess
import atexit
import traceback
from pathlib import Path
from typing import Optional

# Configure logging to both console and debug.log file
log_file = Path("debug.log")
startup_error_log = Path("startup_error.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_base_directory() -> Path:
    """
    Get the base directory for the application.
    Works with both script execution and PyInstaller bundles.
    Uses sys._MEIPASS for PyInstaller to find bundled files.
    """
    if getattr(sys, '_MEIPASS', None):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)
        logger.info(f"Running as PyInstaller bundle. Base path: {base_path}")
        return base_path
    else:
        # Running as script
        base_path = Path(__file__).parent.absolute()
        logger.info(f"Running as script. Base path: {base_path}")
        return base_path


class ServiceManager:
    """
    Process Manager for Ollama, Backend (FastAPI) and Frontend (Streamlit).
    Runs services in threads/processes for the production .exe build.
    """
    
    def __init__(self):
        self.base_dir = get_base_directory()
        self.backend_thread: Optional[threading.Thread] = None
        self.frontend_thread: Optional[threading.Thread] = None
        self.ollama_process: Optional[subprocess.Popen] = None
        self.streamlit_process: Optional[subprocess.Popen] = None
        self.shutdown_event = threading.Event()
        self.backend_should_stop = threading.Event()
        
        # Register cleanup handler
        atexit.register(self.cleanup_processes)
    
    def log_startup_error(self, error_message: str):
        """
        Log startup errors to startup_error.log for troubleshooting.
        """
        try:
            with open(startup_error_log, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Startup Error - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*60}\n")
                f.write(f"{error_message}\n")
        except Exception as e:
            logger.error(f"Failed to write to startup_error.log: {e}")
    
    def start_ollama(self) -> bool:
        """
        Start Ollama server as a background process.
        Sets OLLAMA_MODELS environment variable to point to ./bin/models.
        Returns True if successful, False otherwise.
        """
        try:
            logger.info("Starting Ollama server...")
            
            # Configure Ollama models directory and port
            ollama_models_path = self.base_dir / "bin" / "models"
            os.environ["OLLAMA_MODELS"] = str(ollama_models_path)
            os.environ["OLLAMA_HOST"] = "127.0.0.1:11435"  # Use port 11435 to avoid conflict
            logger.info(f"Set OLLAMA_MODELS to: {ollama_models_path}")
            logger.info(f"Set OLLAMA_HOST to: 127.0.0.1:11435")
            
            # Path to ollama.exe
            ollama_exe = self.base_dir / "bin" / "ollama.exe"
            
            if not ollama_exe.exists():
                error_msg = f"Ollama executable not found at: {ollama_exe}"
                logger.warning(error_msg)
                self.log_startup_error(error_msg)
                return False
            
            # Start Ollama serve as subprocess
            logger.info(f"Launching Ollama from: {ollama_exe}")
            
            # Use CREATE_NO_WINDOW flag on Windows to hide console
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            self.ollama_process = subprocess.Popen(
                [str(ollama_exe), "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
                cwd=str(self.base_dir)
            )
            
            logger.info(f"Ollama process started with PID: {self.ollama_process.pid}")
            
            # Wait 5 seconds for Ollama to initialize
            logger.info("Waiting 5 seconds for Ollama to initialize...")
            time.sleep(5)
            
            # Check if process is still running
            if self.ollama_process.poll() is not None:
                exit_code = self.ollama_process.poll()
                # Check if it's because port is already in use (another Ollama instance)
                if exit_code == 1:
                    logger.info("Ollama port already in use - using existing Ollama instance")
                    self.ollama_process = None  # Don't manage external instance
                    return True  # Ollama is available, just not started by us
                else:
                    error_msg = f"Ollama process terminated unexpectedly with code: {exit_code}"
                    logger.error(error_msg)
                    self.log_startup_error(error_msg)
                    return False
            
            logger.info("Ollama server started successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start Ollama: {e}"
            logger.error(error_msg, exc_info=True)
            self.log_startup_error(f"{error_msg}\n{traceback.format_exc()}")
            return False
    
    def cleanup_processes(self):
        """
        Clean up all processes when shutting down.
        Ensures Streamlit, Ollama and other processes are terminated properly.
        Can be called multiple times safely (idempotent).
        """
        logger.info("Cleaning up processes...")
        
        # Terminate Streamlit process
        if self.streamlit_process:
            try:
                logger.info(f"Terminating Streamlit process (PID: {self.streamlit_process.pid})...")
                self.streamlit_process.terminate()
                try:
                    self.streamlit_process.wait(timeout=5)
                    logger.info("Streamlit process terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("Streamlit process did not terminate gracefully, killing...")
                    self.streamlit_process.kill()
                    self.streamlit_process.wait()
                    logger.info("Streamlit process killed")
            except Exception as e:
                logger.error(f"Error terminating Streamlit process: {e}")
            finally:
                self.streamlit_process = None
        
        # Terminate Ollama process
        if self.ollama_process is not None:
            try:
                logger.info(f"Terminating Ollama process (PID: {self.ollama_process.pid})...")
                self.ollama_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.ollama_process.wait(timeout=5)
                    logger.info("Ollama process terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("Ollama process did not terminate gracefully, killing...")
                    self.ollama_process.kill()
                    self.ollama_process.wait()
                    logger.info("Ollama process killed")
            except Exception as e:
                logger.error(f"Error terminating Ollama process: {e}")
            finally:
                # Mark as cleaned up to prevent duplicate attempts
                self.ollama_process = None
        
        logger.info("Cleanup complete")
        
    def start_backend(self):
        """
        Start the FastAPI backend using uvicorn.run in a thread.
        This is the proper way to run uvicorn programmatically.
        """
        try:
            logger.info("Starting FastAPI backend in thread...")
            
            # Import uvicorn here to avoid import issues
            import uvicorn
            
            # Set working directory to base_dir
            os.chdir(str(self.base_dir))
            
            # Add base directory to Python path so imports work
            if str(self.base_dir) not in sys.path:
                sys.path.insert(0, str(self.base_dir))
            
            # Run uvicorn server
            # Note: This will block until server stops
            uvicorn.run(
                "backend.main:app",
                host="127.0.0.1",
                port=8000,
                log_level="info",
                log_config=None  # Disable default logging config for PyInstaller
            )
            
        except Exception as e:
            logger.error(f"Error in backend thread: {e}", exc_info=True)
            with open("debug.log", "a") as f:
                f.write(f"\n[BACKEND ERROR] {e}\n")
    
    def start_frontend(self):
        """
        Start the Streamlit frontend as a subprocess with visible console window.
        This allows users to see Streamlit logs in real-time.
        """
        try:
            logger.info("Starting Streamlit frontend in subprocess...")
            
            # Set working directory to base_dir
            os.chdir(str(self.base_dir))
            
            # Set environment variable for backend URL
            os.environ['BACKEND_URL'] = 'http://127.0.0.1:8000'
            
            # Determine frontend app path
            frontend_app = self.base_dir / 'frontend' / 'app.py'
            
            if not frontend_app.exists():
                logger.error(f"Frontend app.py not found at: {frontend_app}")
                with open("debug.log", "a") as f:
                    f.write(f"\n[FRONTEND ERROR] app.py not found at {frontend_app}\n")
                return
            
            # Build command to run Streamlit
            streamlit_cmd = [
                sys.executable,  # Use same Python interpreter
                "-m", "streamlit",
                "run",
                str(frontend_app),
                "--server.address=127.0.0.1",
                "--server.port=8501",
                # NOTE: We do NOT use --server.headless=true to allow browser opening
            ]
            
            logger.info(f"Starting Streamlit with command: {' '.join(streamlit_cmd)}")
            
            # Start Streamlit as a subprocess with a visible window
            if sys.platform == "win32":
                # Open new console window on Windows
                self.streamlit_process = subprocess.Popen(
                    streamlit_cmd,
                    cwd=str(self.base_dir),
                    env=os.environ.copy(),
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # On non-Windows platforms, don't use creationflags
                self.streamlit_process = subprocess.Popen(
                    streamlit_cmd,
                    cwd=str(self.base_dir),
                    env=os.environ.copy()
                )
            
            logger.info(f"Streamlit process started with PID: {self.streamlit_process.pid}")
            
            # Wait for Streamlit process to finish
            self.streamlit_process.wait()
            
        except Exception as e:
            logger.error(f"Error in frontend: {e}", exc_info=True)
            with open("debug.log", "a") as f:
                f.write(f"\n[FRONTEND ERROR] {e}\n")
    
    def run(self):
        """
        Main execution method - starts all services.
        Order: Ollama -> Backend -> Frontend
        """
        logger.info("="*60)
        logger.info("Nordic Secure - Golden Master Production Build")
        logger.info("="*60)
        
        try:
            # Set environment variable to indicate running in Windows .exe
            os.environ['IsWindowsApp'] = 'True'
            logger.info("Environment variable IsWindowsApp=True set")
            
            # Step 1: Start Ollama
            logger.info("Step 1: Starting Ollama server...")
            if not self.start_ollama():
                logger.warning("Ollama failed to start. Continuing without Ollama...")
                logger.warning("Some features may not be available.")
            else:
                logger.info("Ollama is ready")
            
            # Step 2: Start backend in a separate thread
            logger.info("Step 2: Starting Backend (FastAPI) in thread...")
            # Use daemon=False to allow proper cleanup
            self.backend_thread = threading.Thread(target=self.start_backend, daemon=False)
            self.backend_thread.start()
            
            # Give backend time to start
            time.sleep(5)
            logger.info("Backend should be running on http://127.0.0.1:8000")
            
            # Step 3: Start frontend in main thread (this will block)
            logger.info("Step 3: Starting Frontend (Streamlit) in main thread...")
            self.start_frontend()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            error_msg = f"Unexpected error in main launcher: {e}"
            logger.error(error_msg, exc_info=True)
            self.log_startup_error(f"{error_msg}\n{traceback.format_exc()}")
        finally:
            logger.info("Shutting down...")
            self.shutdown_event.set()
            self.cleanup_processes()


def main():
    """
    Main entry point for the launcher.
    Logs any startup errors to startup_error.log for troubleshooting.
    """
    try:
        logger.info("Nordic Secure launcher starting...")
        
        # Create and run service manager
        manager = ServiceManager()
        manager.run()
        
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}", exc_info=True)
        
        # Write error to startup_error.log for customer troubleshooting
        try:
            with open(startup_error_log, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"FATAL STARTUP ERROR - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*60}\n")
                f.write(f"{traceback.format_exc()}\n")
        except Exception as log_error:
            # If we can't write to startup_error.log, at least log it to console
            logger.error(f"Failed to write to startup_error.log: {log_error}")
        
        # Also write to debug.log for consistency
        try:
            with open("debug.log", "a") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"FATAL STARTUP ERROR\n")
                f.write(f"{'='*60}\n")
                f.write(f"{traceback.format_exc()}\n")
        except Exception as log_error:
            # If we can't write to debug.log either, at least we tried
            logger.error(f"Failed to write to debug.log: {log_error}")
        
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
