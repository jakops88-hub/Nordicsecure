#!/usr/bin/env python
"""
Nordic Secure Main Launcher - Process Manager
Entry point for the Golden Master production build.
Manages Backend (FastAPI) and Frontend (Streamlit) services.
"""

import os
import sys
import threading
import time
import logging
from pathlib import Path
from typing import Optional

# Configure logging to both console and debug.log file
log_file = Path("debug.log")
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
    Process Manager for Backend (FastAPI) and Frontend (Streamlit).
    Runs services in threads for the production .exe build.
    """
    
    def __init__(self):
        self.base_dir = get_base_directory()
        self.backend_thread: Optional[threading.Thread] = None
        self.frontend_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
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
                log_level="info"
            )
            
        except Exception as e:
            logger.error(f"Error in backend thread: {e}", exc_info=True)
            with open("debug.log", "a") as f:
                f.write(f"\n[BACKEND ERROR] {e}\n")
    
    def start_frontend(self):
        """
        Start the Streamlit frontend using streamlit.web.cli.main.
        This is the proper way to start Streamlit programmatically.
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
            
            # Use Streamlit's CLI main function
            from streamlit.web import cli as stcli
            
            # Set sys.argv for Streamlit CLI
            sys.argv = [
                "streamlit",
                "run",
                str(frontend_app),
                "--server.port=8501",
                "--server.address=127.0.0.1",
                "--server.headless=true"
            ]
            
            # Run Streamlit
            sys.exit(stcli.main())
            
        except Exception as e:
            logger.error(f"Error in frontend: {e}", exc_info=True)
            with open("debug.log", "a") as f:
                f.write(f"\n[FRONTEND ERROR] {e}\n")
    
    def run(self):
        """
        Main execution method - starts all services.
        Backend runs in a thread, Frontend runs in main thread.
        """
        logger.info("="*60)
        logger.info("Nordic Secure - Golden Master Production Build")
        logger.info("="*60)
        
        try:
            # Set environment variable to indicate running in Windows .exe
            os.environ['IsWindowsApp'] = 'True'
            logger.info("Environment variable IsWindowsApp=True set")
            
            # Start backend in a separate thread
            logger.info("Starting Backend (FastAPI) in thread...")
            self.backend_thread = threading.Thread(target=self.start_backend, daemon=True)
            self.backend_thread.start()
            
            # Give backend time to start
            time.sleep(5)
            logger.info("Backend should be running on http://127.0.0.1:8000")
            
            # Start frontend in main thread (this will block)
            logger.info("Starting Frontend (Streamlit) in main thread...")
            self.start_frontend()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error in main launcher: {e}", exc_info=True)
            with open("debug.log", "a") as f:
                f.write(f"\n[MAIN ERROR] {e}\n")
        finally:
            logger.info("Shutting down...")
            self.shutdown_event.set()


def main():
    """
    Main entry point for the launcher.
    Logs any startup errors to debug.log for troubleshooting.
    """
    try:
        logger.info("Nordic Secure launcher starting...")
        
        # Create and run service manager
        manager = ServiceManager()
        manager.run()
        
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}", exc_info=True)
        
        # Write error to debug.log for customer troubleshooting
        try:
            with open("debug.log", "a") as f:
                import traceback
                f.write(f"\n{'='*60}\n")
                f.write(f"FATAL STARTUP ERROR\n")
                f.write(f"{'='*60}\n")
                f.write(f"{traceback.format_exc()}\n")
        except:
            pass
        
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
