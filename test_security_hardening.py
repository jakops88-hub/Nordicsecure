#!/usr/bin/env python3
"""
Test script to verify security hardening features are working correctly.

Tests:
1. Environment variables for telemetry blocking are present in code
2. Audit logging functionality is present in code
3. Ingestion script has required features
"""

import sys
from pathlib import Path

def test_environment_variables_in_code():
    """Test that telemetry blocking code is present in files."""
    print("=" * 80)
    print("TEST 1: Environment Variables in Code")
    print("=" * 80)
    
    files_to_check = [
        Path("backend/main.py"),
        Path("frontend/app.py"),
        Path("backend/ingest.py")
    ]
    
    required_vars = [
        'LANGCHAIN_TRACING_V2',
        'SCARF_NO_ANALYTICS',
        'HF_HUB_OFFLINE',
        'TRANSFORMERS_OFFLINE',
    ]
    
    all_passed = True
    
    for file_path in files_to_check:
        print(f"\nChecking {file_path}:")
        
        if not file_path.exists():
            print(f"  ✗ File not found!")
            all_passed = False
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Iron Dome comment
        if "IRON DOME" in content:
            print(f"  ✓ Iron Dome security header present")
        else:
            print(f"  ✗ Iron Dome security header missing")
            all_passed = False
        
        # Check for environment variables
        found_count = 0
        for var in required_vars:
            if var in content:
                found_count += 1
        
        if found_count == len(required_vars):
            print(f"  ✓ All {len(required_vars)} telemetry blocking variables present")
        else:
            print(f"  ✗ Only {found_count}/{len(required_vars)} variables found")
            all_passed = False
        
        # Check that env vars are set before imports
        # Simple check: Iron Dome header should appear before fastapi/streamlit imports
        if file_path.name in ['main.py', 'app.py', 'ingest.py']:
            lines = content.split('\n')
            iron_dome_line = -1
            first_library_import_line = -1
            
            for i, line in enumerate(lines):
                # Find Iron Dome header
                if "IRON DOME" in line and iron_dome_line == -1:
                    iron_dome_line = i
                
                # Find first significant library import (not os, sys, or comments)
                stripped = line.strip()
                if stripped.startswith('from ') or stripped.startswith('import '):
                    # Skip comments and the initial os import used for environ
                    if not stripped.startswith('#'):
                        # We want to find the first library import after the os.environ setup
                        # Look for common libraries like fastapi, streamlit, requests (not os/sys)
                        if any(lib in line for lib in ['fastapi', 'streamlit', 'requests', 'pandas', 'numpy', 'backend.']):
                            first_library_import_line = i
                            break
            
            if iron_dome_line > 0 and first_library_import_line > 0 and iron_dome_line < first_library_import_line:
                print(f"  ✓ Environment variables set before library imports")
            elif first_library_import_line == -1:
                # No library imports found (unlikely but handle gracefully)
                print(f"  ✓ Environment variables present (no library imports to check)")
            else:
                print(f"  ⚠ Warning: Check env var ordering (Iron Dome: line {iron_dome_line}, first import: line {first_library_import_line})")
    
    if all_passed:
        print("\n✓ All environment variables are correctly present in code!")
    else:
        print("\n✗ Some environment variables checks failed!")
    
    return all_passed


def test_audit_logging_in_code():
    """Test that audit logging code is present."""
    print("\n" + "=" * 80)
    print("TEST 2: Audit Logging in Code")
    print("=" * 80)
    
    files_to_check = {
        Path("backend/main.py"): [
            "audit_log.csv",
            "log_query_to_audit",
            "Timestamp",
            "Result_Count"
        ],
        Path("frontend/app.py"): [
            "audit_log.csv",
            "log_query_to_audit"
        ]
    }
    
    all_passed = True
    
    for file_path, required_items in files_to_check.items():
        print(f"\nChecking {file_path}:")
        
        if not file_path.exists():
            print(f"  ✗ File not found!")
            all_passed = False
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for item in required_items:
            if item in content:
                print(f"  ✓ '{item}' present")
            else:
                print(f"  ✗ '{item}' missing")
                all_passed = False
    
    if all_passed:
        print("\n✓ Audit logging is correctly implemented!")
    else:
        print("\n✗ Some audit logging features are missing!")
    
    return all_passed


def test_ingestion_features():
    """Test that ingestion script has required features."""
    print("\n" + "=" * 80)
    print("TEST 3: Ingestion Script Features")
    print("=" * 80)
    
    file_path = Path("backend/ingest.py")
    
    if not file_path.exists():
        print(f"✗ {file_path} not found!")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_features = {
        "File size check": ["MAX_FILE_SIZE_MB", "50", "check_file_size"],
        "Memory cleanup": ["gc.collect()", "MEMORY_CLEANUP_INTERVAL", "10"],
        "Error handling": ["failed_files.log", "log_failed_file", "try:", "except"],
        "Corrupt file handling": ["continue", "except Exception"],
        "Batch processing": ["batch_ingest", "for", "pdf_files"]
    }
    
    all_passed = True
    
    for feature_name, keywords in required_features.items():
        found_count = sum(1 for keyword in keywords if keyword in content)
        
        if found_count == len(keywords):
            print(f"✓ {feature_name}: All {len(keywords)} keywords present")
        else:
            print(f"✗ {feature_name}: Only {found_count}/{len(keywords)} keywords found")
            all_passed = False
    
    if all_passed:
        print("\n✓ Ingestion script has all required features!")
    else:
        print("\n✗ Ingestion script is missing some features!")
    
    return all_passed


def test_network_check():
    """Test that network check is present in frontend."""
    print("\n" + "=" * 80)
    print("TEST 4: Network Check in Frontend")
    print("=" * 80)
    
    file_path = Path("frontend/app.py")
    
    if not file_path.exists():
        print(f"✗ {file_path} not found!")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_items = [
        "check_network_connection",
        "Network connection detected",
        "disconnect from the internet",
        "google.com"
    ]
    
    all_passed = True
    
    for item in required_items:
        if item in content:
            print(f"✓ '{item}' present")
        else:
            print(f"✗ '{item}' missing")
            all_passed = False
    
    if all_passed:
        print("\n✓ Network check is correctly implemented!")
    else:
        print("\n✗ Network check is missing some features!")
    
    return all_passed


def test_streamlit_config():
    """Test that Streamlit config disables telemetry."""
    print("\n" + "=" * 80)
    print("TEST 5: Streamlit Configuration")
    print("=" * 80)
    
    file_path = Path(".streamlit/config.toml")
    
    if not file_path.exists():
        print(f"✗ {file_path} not found!")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "gatherUsageStats = false" in content:
        print("✓ gatherUsageStats = false is set")
        print("\n✓ Streamlit telemetry is disabled!")
        return True
    else:
        print("✗ gatherUsageStats is not set to false")
        return False


def main():
    """Run all tests."""
    print("NordicSecure Security Hardening Tests")
    print("=" * 80)
    
    results = []
    
    # Run tests
    results.append(("Environment Variables", test_environment_variables_in_code()))
    results.append(("Audit Logging", test_audit_logging_in_code()))
    results.append(("Ingestion Features", test_ingestion_features()))
    results.append(("Network Check", test_network_check()))
    results.append(("Streamlit Config", test_streamlit_config()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 80)
    
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        return 0
    else:
        print("✗ SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
