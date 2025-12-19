"""
License verification module for Nordic Secure.

This module provides offline license verification using asymmetric cryptography (Ed25519).
Licenses are signed with a private key and verified using a hardcoded public key.
"""

import os
import json
import base64
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

# Configure logger
logger = logging.getLogger(__name__)


class LicenseExpiredError(Exception):
    """Exception raised when a license has expired."""
    pass


class LicenseInvalidError(Exception):
    """Exception raised when a license is invalid or tampered with."""
    pass


class LicenseVerifier:
    """
    Verifies offline licenses using Ed25519 cryptographic signatures.
    
    The license format is a base64-encoded JSON object containing:
    - customer: Customer name
    - expiration_date: ISO format date (YYYY-MM-DD)
    - signature: Ed25519 signature of the license data
    """
    
    # Actual production public key for license verification
    # This is a base64-encoded Ed25519 public key (32 bytes)
    # Generated from the private key kept secure by the administrator
    PUBLIC_KEY_B64 = "t4XAMrwiV59V3EPyiHCEwG7/TEDoRSpkRlCtFPpdaBA="
    
    def __init__(self):
        """Initialize the license verifier with the hardcoded public key."""
        try:
            public_key_bytes = base64.b64decode(self.PUBLIC_KEY_B64)
            self.public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        except Exception as e:
            raise RuntimeError(f"Failed to load public key: {e}")
    
    def _read_license(self) -> Optional[str]:
        """
        Read the license from file or environment variable.
        
        Priority:
        1. NORDIC_LICENSE environment variable
        2. license.key file in the current directory
        
        Returns:
            License string or None if not found
        """
        # Try environment variable first
        license_str = os.getenv("NORDIC_LICENSE")
        if license_str:
            return license_str
        
        # Try license.key file
        license_file_paths = [
            "license.key",
            "/app/license.key"
        ]
        
        for license_path in license_file_paths:
            if os.path.exists(license_path):
                try:
                    with open(license_path, "r") as f:
                        return f.read().strip()
                except Exception as e:
                    logger.warning(f"Failed to read license file {license_path}: {e}")
        
        return None
    
    def _verify_signature(self, data: bytes, signature: bytes) -> bool:
        """
        Verify the Ed25519 signature of the data.
        
        Args:
            data: The data that was signed
            signature: The signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            self.public_key.verify(signature, data)
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            logger.warning(f"Signature verification error: {e}")
            return False
    
    def check_license(self) -> Dict[str, Any]:
        """
        Check if the license is valid and not expired.
        
        Returns:
            Dictionary with license information (customer, expiration_date)
            
        Raises:
            LicenseInvalidError: If license is missing, invalid, or tampered with
            LicenseExpiredError: If license has expired
        """
        # Read license
        license_str = self._read_license()
        if not license_str:
            raise LicenseInvalidError("License not found. Please set NORDIC_LICENSE environment variable or create license.key file.")
        
        try:
            # Decode base64 license
            license_bytes = base64.b64decode(license_str)
            license_data = json.loads(license_bytes.decode('utf-8'))
            
            # Validate required fields
            required_fields = ["customer", "expiration_date", "signature"]
            for field in required_fields:
                if field not in license_data:
                    raise LicenseInvalidError(f"Invalid license format: missing {field}")
            
            # Extract signature and create data to verify
            signature_b64 = license_data["signature"]
            signature = base64.b64decode(signature_b64)
            
            # Create canonical representation of data (without signature)
            data_to_verify = {
                "customer": license_data["customer"],
                "expiration_date": license_data["expiration_date"]
            }
            data_bytes = json.dumps(data_to_verify, sort_keys=True).encode('utf-8')
            
            # Verify signature
            if not self._verify_signature(data_bytes, signature):
                raise LicenseInvalidError("Invalid license signature. License may be tampered with.")
            
            # Check expiration date
            try:
                # Parse expiration date (assume UTC if no timezone specified)
                expiration_date_str = license_data["expiration_date"]
                expiration_date = datetime.fromisoformat(expiration_date_str)
                
                # If naive datetime (no timezone), assume UTC
                if expiration_date.tzinfo is None:
                    expiration_date = expiration_date.replace(tzinfo=timezone.utc)
            except ValueError as e:
                raise LicenseInvalidError(
                    f"Invalid expiration date format. Expected ISO format (YYYY-MM-DD): {str(e)}"
                )
            
            # Get current time in UTC
            current_date = datetime.now(timezone.utc)
            
            if current_date > expiration_date:
                raise LicenseExpiredError(
                    f"License expired on {license_data['expiration_date']}. "
                    "Contact support to renew."
                )
            
            # Return license info
            return {
                "customer": license_data["customer"],
                "expiration_date": license_data["expiration_date"],
                "valid": True
            }
            
        except LicenseExpiredError:
            raise
        except LicenseInvalidError:
            raise
        except json.JSONDecodeError:
            raise LicenseInvalidError("Invalid license format: not valid JSON")
        except Exception as e:
            raise LicenseInvalidError(f"License verification failed: {str(e)}")


# Singleton instance
_verifier = None


def get_license_verifier() -> LicenseVerifier:
    """
    Get the singleton license verifier instance.
    
    Returns:
        LicenseVerifier instance
    """
    global _verifier
    if _verifier is None:
        _verifier = LicenseVerifier()
    return _verifier
