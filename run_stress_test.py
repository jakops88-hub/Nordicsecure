#!/usr/bin/env python3
"""
Quick Start Stress Test Runner
================================

This script sets up and runs the stress tests automatically.
It will:
1. Check dependencies
2. Install missing packages if needed
3. Run the stress test
4. Display results

Usage:
    python run_stress_test.py [options]

Options:
    --backend-only    Run backend stress test only (no API)
    --live           Run live app stress test (requires backend running)
    --pdfs N         Number of PDFs to test with (default: 50)
    --help           Show this help message
"""

import sys
import subprocess
import os
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def check_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_packages(packages):
    """Install missing Python packages."""
    print_info(f"Installing packages: {', '.join(packages)}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q"] + packages,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install packages: {e}")
        return False

def check_dependencies():
    """Check and install required dependencies."""
    print_header("Checking Dependencies")
    
    # Required packages for stress tests
    required_packages = {
        'psutil': 'psutil',
        'reportlab': 'reportlab',
        'PyPDF2': 'PyPDF2',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        if check_package(import_name):
            print_success(f"{package_name} is installed")
        else:
            print_warning(f"{package_name} is NOT installed")
            missing_packages.append(package_name)
    
    if missing_packages:
        print_info(f"Installing {len(missing_packages)} missing packages...")
        if install_packages(missing_packages):
            print_success("All dependencies installed successfully!")
            return True
        else:
            print_error("Failed to install some dependencies")
            return False
    else:
        print_success("All dependencies are installed!")
        return True

def check_backend_running():
    """Check if the backend is running."""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def run_backend_stress_test(num_pdfs=50):
    """Run the backend stress test."""
    print_header("Running Backend Stress Test")
    print_info(f"Testing with {num_pdfs} PDF files")
    print_info("This tests PDF processing directly (no API layer)")
    print()
    
    # Check if test file exists
    test_file = Path("backend/test_pdf_stress.py")
    if not test_file.exists():
        print_error(f"Test file not found: {test_file}")
        return False
    
    # Modify the test file temporarily to use the specified number of PDFs
    # We'll pass it as an environment variable
    os.environ['STRESS_TEST_NUM_PDFS'] = str(num_pdfs)
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=Path.cwd()
        )
        return result.returncode == 0
    except Exception as e:
        print_error(f"Failed to run backend stress test: {e}")
        return False

def run_live_stress_test(num_pdfs=50):
    """Run the live app stress test."""
    print_header("Running Live App Stress Test")
    print_info(f"Testing with {num_pdfs} PDF files")
    print_info("This tests the full stack via API")
    print()
    
    # Check if backend is running
    print_info("Checking if backend is running...")
    if not check_backend_running():
        print_error("Backend is not running!")
        print_info("Please start the backend first:")
        print_info("  python backend/main.py")
        return False
    
    print_success("Backend is running and healthy")
    print()
    
    # Check if test file exists
    test_file = Path("stress_test_live.py")
    if not test_file.exists():
        print_error(f"Test file not found: {test_file}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=Path.cwd()
        )
        return result.returncode == 0
    except Exception as e:
        print_error(f"Failed to run live stress test: {e}")
        return False

def print_usage():
    """Print usage information."""
    print(__doc__)

def main():
    """Main entry point."""
    # Parse command line arguments
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print_usage()
        return 0
    
    backend_only = '--backend-only' in args
    live_only = '--live' in args
    
    # Get number of PDFs
    num_pdfs = 50
    if '--pdfs' in args:
        try:
            idx = args.index('--pdfs')
            num_pdfs = int(args[idx + 1])
        except (IndexError, ValueError):
            print_error("Invalid --pdfs argument. Using default: 50")
    
    print_header("Nordic Secure Stress Test Runner")
    print_info(f"Testing with {num_pdfs} PDF files")
    print()
    
    # Check dependencies
    if not check_dependencies():
        print_error("Dependency check failed. Please install manually:")
        print_info("  pip install psutil reportlab PyPDF2 requests")
        return 1
    
    # Run tests based on arguments
    success = True
    
    if not live_only:
        # Run backend stress test
        success = run_backend_stress_test(num_pdfs) and success
    
    if not backend_only:
        # Run live stress test
        print()
        success = run_live_stress_test(num_pdfs) and success
    
    # Final summary
    print()
    print_header("Stress Test Complete")
    
    if success:
        print_success("All tests completed successfully!")
        print_info("Check the generated report files for detailed statistics")
        print_info("Report files:")
        print_info("  - stress_test_report_*.txt (backend test)")
        print_info("  - live_stress_test_report_*.txt (live app test)")
    else:
        print_error("Some tests failed. Please check the output above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
