#!/usr/bin/env python
"""
Nordic Secure Main Launcher
Orchestrates all services (Ollama, Backend, Frontend) for native Windows deployment.
"""

import os
import sys
import subprocess
import multiprocessing
import time
import signal
import logging
from pathlib import Path
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_base_directory() -> Path:
    """
    Get the base directory for the application.
    Works with both script execution and PyInstaller bundles.
    """
    if getattr(sys, '_MEIPASS', None):
        # Running as PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running as script
        return Path(__file__).parent.absolute()


def get_ollama_path() -> Optional[Path]:
    """
    Get the path to the Ollama executable.
    Looks in bin/ directory relative to the application.
    """
    base_dir = get_base_directory()
    ollama_path = base_dir / 'bin' / 'ollama.exe'
    
    if ollama_path.exists():
        logger.info(f"Found Ollama at: {ollama_path}")
        return ollama_path
    else:
        logger.warning(f"Ollama not found at: {ollama_path}")
        return None


class ServiceManager:
    """
    Manages the lifecycle of all services (Ollama, Backend, Frontend).
    """
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.base_dir = get_base_directory()
        self.ollama_process: Optional[subprocess.Popen] = None
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        
    def start_ollama(self) -> bool:
        """
        Start the Ollama server.
        
        Returns:
            True if started successfully, False otherwise
        """
        ollama_path = get_ollama_path()
        
        if not ollama_path:
            logger.error("Ollama executable not found. Please place ollama.exe in the bin/ directory.")
            return False
        
        try:
            logger.info("Starting Ollama server...")
            
            # Start Ollama serve
            self.ollama_process = subprocess.Popen(
                [str(ollama_path), "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            self.processes.append(self.ollama_process)
            
            # Wait a bit for Ollama to start
            time.sleep(5)
            
            # Check if process is still running
            if self.ollama_process.poll() is None:
                logger.info("Ollama server started successfully")
                return True
            else:
                logger.error("Ollama server failed to start")
                return False
            
        except Exception as e:
            logger.error(f"Error starting Ollama: {e}")
            return False
    
    def start_backend(self) -> bool:
        """
        Start the FastAPI backend using uvicorn.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            logger.info("Starting FastAPI backend...")
            
            # Determine backend main file path
            backend_main = self.base_dir / 'backend' / 'main.py'
            
            if not backend_main.exists():
                logger.error(f"Backend main.py not found at: {backend_main}")
                return False
            
            # Start uvicorn programmatically in a subprocess
            # This allows better process management
            self.backend_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m", "uvicorn",
                    "backend.main:app",
                    "--host", "127.0.0.1",
                    "--port", "8000"
                ],
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            self.processes.append(self.backend_process)
            
            # Wait for backend to start
            time.sleep(3)
            
            # Check if process is still running
            if self.backend_process.poll() is None:
                logger.info("FastAPI backend started successfully on http://127.0.0.1:8000")
                return True
            else:
                logger.error("FastAPI backend failed to start")
                return False
            
        except Exception as e:
            logger.error(f"Error starting backend: {e}")
            return False
    
    def start_frontend(self) -> bool:
        """
        Start the Streamlit frontend.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            logger.info("Starting Streamlit frontend...")
            
            # Determine frontend app path
            frontend_app = self.base_dir / 'frontend' / 'app.py'
            
            if not frontend_app.exists():
                logger.error(f"Frontend app.py not found at: {frontend_app}")
                return False
            
            # Set environment variable for backend URL
            env = os.environ.copy()
            env['BACKEND_URL'] = 'http://127.0.0.1:8000'
            
            # Start Streamlit
            self.frontend_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m", "streamlit",
                    "run",
                    str(frontend_app),
                    "--server.port", "8501",
                    "--server.address", "127.0.0.1"
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            self.processes.append(self.frontend_process)
            
            # Wait for frontend to start
            time.sleep(3)
            
            # Check if process is still running
            if self.frontend_process.poll() is None:
                logger.info("Streamlit frontend started successfully on http://127.0.0.1:8501")
                return True
            else:
                logger.error("Streamlit frontend failed to start")
                return False
            
        except Exception as e:
            logger.error(f"Error starting frontend: {e}")
            return False
    
    def stop_all(self):
        """
        Stop all running services gracefully.
        """
        logger.info("Stopping all services...")
        
        # Stop in reverse order
        for process in reversed(self.processes):
            if process and process.poll() is None:
                try:
                    # Try graceful termination first
                    process.terminate()
                    
                    # Wait up to 5 seconds for graceful shutdown
                    try:
                        process.wait(timeout=5)
                        logger.info(f"Process {process.pid} terminated gracefully")
                    except subprocess.TimeoutExpired:
                        # Force kill if graceful shutdown fails
                        process.kill()
                        logger.warning(f"Process {process.pid} force killed")
                
                except Exception as e:
                    logger.error(f"Error stopping process: {e}")
        
        self.processes.clear()
        logger.info("All services stopped")
    
    def run(self):
        """
        Main execution method - starts all services and monitors them.
        """
        logger.info("="*60)
        logger.info("Nordic Secure - Starting all services")
        logger.info("="*60)
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, lambda s, f: self.handle_shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.handle_shutdown())
        
        try:
            # Start services in order
            if not self.start_ollama():
                logger.error("Failed to start Ollama. Exiting.")
                return 1
            
            if not self.start_backend():
                logger.error("Failed to start backend. Exiting.")
                self.stop_all()
                return 1
            
            if not self.start_frontend():
                logger.error("Failed to start frontend. Exiting.")
                self.stop_all()
                return 1
            
            logger.info("="*60)
            logger.info("All services started successfully!")
            logger.info("Frontend: http://127.0.0.1:8501")
            logger.info("Backend API: http://127.0.0.1:8000")
            logger.info("Press Ctrl+C to stop all services")
            logger.info("="*60)
            
            # Monitor processes
            self.monitor_processes()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.stop_all()
        
        return 0
    
    def monitor_processes(self):
        """
        Monitor all processes and restart if any crashes.
        """
        while True:
            time.sleep(5)
            
            # Check each process
            if self.ollama_process and self.ollama_process.poll() is not None:
                logger.error("Ollama process died. Restarting...")
                self.start_ollama()
            
            if self.backend_process and self.backend_process.poll() is not None:
                logger.error("Backend process died. Restarting...")
                self.start_backend()
            
            if self.frontend_process and self.frontend_process.poll() is not None:
                logger.error("Frontend process died. Restarting...")
                self.start_frontend()
    
    def handle_shutdown(self):
        """
        Handle shutdown signals gracefully.
        """
        logger.info("Shutdown signal received")
        self.stop_all()
        sys.exit(0)


def main():
    """
    Main entry point for the launcher.
    """
    # Prevent multiple instances
    multiprocessing.freeze_support()
    
    # Create and run service manager
    manager = ServiceManager()
    return manager.run()


if __name__ == "__main__":
    sys.exit(main())
