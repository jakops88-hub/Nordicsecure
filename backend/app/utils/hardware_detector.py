"""
Hardware Detection Utility - Detects GPU/CPU capabilities for model acceleration
"""

import logging
import platform
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HardwareDetector:
    """
    Detects available hardware acceleration capabilities.
    
    Supports:
    - NVIDIA CUDA GPUs
    - Apple Silicon (M1/M2/M3) with Metal
    - CPU fallback
    """
    
    def __init__(self):
        self._hardware_info = None
    
    def detect_hardware(self) -> Dict[str, any]:
        """
        Detect available hardware acceleration.
        
        Returns:
            Dictionary containing:
            - device: str ('cuda', 'mps', 'cpu')
            - device_name: str (GPU name or 'CPU')
            - cuda_available: bool
            - mps_available: bool
            - gpu_layers: int (number of layers to offload, -1 for all)
            - backend: str ('cuda', 'metal', 'cpu')
        """
        if self._hardware_info is not None:
            return self._hardware_info
        
        cuda_available = False
        mps_available = False
        device = 'cpu'
        device_name = 'CPU'
        gpu_layers = 0
        backend = 'cpu'
        
        # Check for CUDA (NVIDIA GPU)
        try:
            import torch
            if torch.cuda.is_available():
                cuda_available = True
                device = 'cuda'
                device_name = torch.cuda.get_device_name(0)
                gpu_layers = -1  # Offload all layers
                backend = 'cuda'
                logger.info(f"CUDA GPU detected: {device_name}")
        except ImportError:
            logger.debug("PyTorch not available, skipping CUDA detection")
        except Exception as e:
            logger.warning(f"Error detecting CUDA: {e}")
        
        # Check for Apple Silicon (MPS)
        if not cuda_available:
            try:
                import torch
                # Check if running on macOS with Apple Silicon
                if platform.system() == 'Darwin' and platform.machine() == 'arm64':
                    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        mps_available = True
                        device = 'mps'
                        device_name = f'Apple Silicon ({platform.processor()})'
                        gpu_layers = -1  # Offload all layers
                        backend = 'metal'
                        logger.info(f"Apple Silicon detected: {device_name}")
            except ImportError:
                logger.debug("PyTorch not available, skipping MPS detection")
            except Exception as e:
                logger.warning(f"Error detecting MPS: {e}")
        
        # Fallback to CPU
        if not cuda_available and not mps_available:
            logger.info("No GPU acceleration available, using CPU")
            device = 'cpu'
            device_name = 'CPU'
            gpu_layers = 0
            backend = 'cpu'
        
        self._hardware_info = {
            'device': device,
            'device_name': device_name,
            'cuda_available': cuda_available,
            'mps_available': mps_available,
            'gpu_layers': gpu_layers,
            'backend': backend
        }
        
        return self._hardware_info
    
    def get_sentence_transformer_device(self) -> str:
        """
        Get the device string for sentence-transformers.
        
        Returns:
            Device string ('cuda', 'mps', or 'cpu')
        """
        hardware = self.detect_hardware()
        return hardware['device']
    
    def get_llama_cpp_params(self) -> Dict[str, any]:
        """
        Get parameters for llama-cpp-python initialization.
        
        Returns:
            Dictionary with n_gpu_layers and other relevant params
        """
        hardware = self.detect_hardware()
        
        params = {
            'n_gpu_layers': hardware['gpu_layers'],
        }
        
        # Add Metal support for Apple Silicon
        if hardware['mps_available']:
            params['n_gpu_layers'] = -1  # Use all layers on Metal
        
        return params
    
    def log_hardware_info(self):
        """Log detected hardware information."""
        hardware = self.detect_hardware()
        logger.info("=" * 60)
        logger.info("Hardware Detection Results:")
        logger.info(f"  Device: {hardware['device']}")
        logger.info(f"  Device Name: {hardware['device_name']}")
        logger.info(f"  CUDA Available: {hardware['cuda_available']}")
        logger.info(f"  MPS Available: {hardware['mps_available']}")
        logger.info(f"  GPU Layers: {hardware['gpu_layers']}")
        logger.info(f"  Backend: {hardware['backend']}")
        logger.info("=" * 60)


# Global singleton instance
_hardware_detector = None


def get_hardware_detector() -> HardwareDetector:
    """Get or create the global hardware detector instance."""
    global _hardware_detector
    if _hardware_detector is None:
        _hardware_detector = HardwareDetector()
    return _hardware_detector
