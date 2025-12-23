"""
Tests for hardware detection and GPU acceleration.

Run with: python test_hardware_detection.py
"""

import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.utils.hardware_detector import HardwareDetector, get_hardware_detector


def test_hardware_detector_initialization():
    """Test that HardwareDetector can be initialized."""
    print("Testing HardwareDetector initialization...")
    
    detector = HardwareDetector()
    assert detector is not None
    
    print("✓ HardwareDetector initialization test passed")


def test_hardware_detection():
    """Test hardware detection logic."""
    print("\nTesting hardware detection...")
    
    detector = HardwareDetector()
    hardware = detector.detect_hardware()
    
    # Check that all expected keys are present
    assert 'device' in hardware
    assert 'device_name' in hardware
    assert 'cuda_available' in hardware
    assert 'mps_available' in hardware
    assert 'gpu_layers' in hardware
    assert 'backend' in hardware
    
    # Device should be one of the valid options
    assert hardware['device'] in ['cuda', 'mps', 'cpu']
    
    # Backend should be one of the valid options
    assert hardware['backend'] in ['cuda', 'metal', 'cpu']
    
    # GPU layers should be -1 (all) for GPU, 0 for CPU
    if hardware['device'] == 'cpu':
        assert hardware['gpu_layers'] == 0
    else:
        assert hardware['gpu_layers'] == -1
    
    print(f"  Detected device: {hardware['device']}")
    print(f"  Device name: {hardware['device_name']}")
    print(f"  CUDA available: {hardware['cuda_available']}")
    print(f"  MPS available: {hardware['mps_available']}")
    print(f"  GPU layers: {hardware['gpu_layers']}")
    print(f"  Backend: {hardware['backend']}")
    
    print("✓ Hardware detection test passed")


def test_get_sentence_transformer_device():
    """Test getting device for sentence-transformers."""
    print("\nTesting sentence-transformers device selection...")
    
    detector = HardwareDetector()
    device = detector.get_sentence_transformer_device()
    
    assert device in ['cuda', 'mps', 'cpu']
    
    print(f"  Sentence-transformers device: {device}")
    print("✓ Sentence-transformers device test passed")


def test_get_llama_cpp_params():
    """Test getting parameters for llama-cpp-python."""
    print("\nTesting llama-cpp-python parameters...")
    
    detector = HardwareDetector()
    params = detector.get_llama_cpp_params()
    
    assert 'n_gpu_layers' in params
    assert isinstance(params['n_gpu_layers'], int)
    assert params['n_gpu_layers'] >= -1
    
    print(f"  n_gpu_layers: {params['n_gpu_layers']}")
    print("✓ llama-cpp-python parameters test passed")


def test_singleton_instance():
    """Test that get_hardware_detector returns singleton."""
    print("\nTesting singleton pattern...")
    
    detector1 = get_hardware_detector()
    detector2 = get_hardware_detector()
    
    assert detector1 is detector2
    
    print("✓ Singleton pattern test passed")


def test_log_hardware_info():
    """Test logging hardware information."""
    print("\nTesting hardware info logging...")
    
    detector = HardwareDetector()
    detector.log_hardware_info()
    
    print("✓ Hardware info logging test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Hardware Detection Tests")
    print("=" * 60)
    
    try:
        test_hardware_detector_initialization()
        test_hardware_detection()
        test_get_sentence_transformer_device()
        test_get_llama_cpp_params()
        test_singleton_instance()
        test_log_hardware_info()
        
        print("\n" + "=" * 60)
        print("All hardware detection tests passed! ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
