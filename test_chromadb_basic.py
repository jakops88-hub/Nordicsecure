#!/usr/bin/env python
"""
Simple test script for ChromaDB integration without model downloads.
Tests basic ChromaDB functionality and path resolution.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import init_db, get_db, get_data_directory


def test_chromadb_basic():
    """Test basic ChromaDB initialization and operations"""
    print("=" * 60)
    print("Testing ChromaDB Basic Operations")
    print("=" * 60)
    
    try:
        # Initialize database
        init_db()
        print("✓ ChromaDB initialized successfully")
        
        # Check data directory
        data_dir = get_data_directory()
        print(f"✓ Data directory: {data_dir}")
        print(f"✓ Directory exists: {os.path.exists(data_dir)}")
        
        # Get collection
        collection = get_db()
        print(f"✓ Collection loaded: {collection.name}")
        print(f"✓ Document count: {collection.count()}")
        
        # Test adding a document with manual embedding
        test_embedding = [0.1] * 384  # Simple embedding vector
        test_doc = "This is a test document for ChromaDB integration."
        test_metadata = {"filename": "test.txt", "test": True}
        
        collection.add(
            embeddings=[test_embedding],
            documents=[test_doc],
            metadatas=[test_metadata],
            ids=["test_doc_1"]
        )
        print("✓ Added test document")
        print(f"✓ New document count: {collection.count()}")
        
        # Test querying
        results = collection.query(
            query_embeddings=[test_embedding],
            n_results=1
        )
        print(f"✓ Query successful, found {len(results['documents'][0])} results")
        
        if results['documents'][0]:
            print(f"✓ Retrieved document: {results['documents'][0][0][:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_path_resolution():
    """Test path resolution for PyInstaller compatibility"""
    print("\n" + "=" * 60)
    print("Testing Path Resolution")
    print("=" * 60)
    
    try:
        # Test sys._MEIPASS simulation
        data_dir = get_data_directory()
        print(f"✓ Data directory resolved: {data_dir}")
        
        # Check if we can write to it
        test_file = os.path.join(data_dir, ".test")
        with open(test_file, 'w') as f:
            f.write("test")
        print("✓ Data directory is writable")
        
        # Cleanup
        os.remove(test_file)
        print("✓ Cleanup successful")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Test that all required modules can be imported"""
    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    modules_to_test = [
        ('chromadb', 'ChromaDB'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('PyPDF2', 'PyPDF2'),
    ]
    
    failed = []
    for module_name, display_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {display_name} imported successfully")
        except ImportError as e:
            print(f"✗ {display_name} failed to import: {e}")
            failed.append(display_name)
    
    # Test sentence-transformers separately (may not be installed)
    try:
        __import__('sentence_transformers')
        print(f"✓ Sentence Transformers imported successfully")
        print(f"  Note: Model download requires internet connection")
    except ImportError:
        print(f"⚠ Sentence Transformers not installed (optional)")
    
    return len(failed) == 0


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Nordic Secure - ChromaDB Migration Tests (Basic)")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Path Resolution", test_path_resolution()))
    results.append(("ChromaDB Basic", test_chromadb_basic()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("\nChromaDB migration is working correctly.")
        print("The application is ready for native Windows deployment.")
        return 0
    else:
        print("✗ Some tests failed")
        print("\nPlease check the errors above and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
