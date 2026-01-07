"""
License Validator Module for NordicSecure
The Lock - Verifies license keys in the main application
"""

import hmac
import hashlib
from datetime import datetime
from typing import Tuple

# Shared secret salt for HMAC verification (must match admin_keygen.py)
# SECURITY NOTE: In production, consider loading this from environment variables
# or secure configuration to prevent exposure if source code is compromised.
# For now, this is hardcoded per requirements for simplicity.
SECRET_SALT = "NordicSecure_2026_HMAC_Secret_Salt_DO_NOT_SHARE"


def verify_license_key(key_string: str) -> Tuple[bool, str]:
    """
    Verify a license key for validity and expiration.
    
    This function performs two critical checks:
    1. Anti-tamper check: Verifies the HMAC signature matches
    2. Expiration check: Ensures the license hasn't expired
    
    Args:
        key_string: License key in format CUSTOMERNAME-EXPIRYDATE-SIGNATURE
        
    Returns:
        Tuple of (is_valid, message):
            - (True, "License is valid") if all checks pass
            - (False, error_message) if any check fails
    
    Examples:
        >>> verify_license_key("JOHNDOE-20260108-a1b2c3d4e5f6g7h8")
        (True, "License is valid")
        
        >>> verify_license_key("JOHNDOE-20230101-invalid")
        (False, "License has expired")
    """
    try:
        # Step 1: Parse the license key
        parts = key_string.split('-')
        
        if len(parts) != 3:
            return (False, "Invalid license key format. Expected: NAME-EXPIRY-SIGNATURE")
        
        customer_name = parts[0]
        expiry_date_str = parts[1]
        provided_signature = parts[2]
        
        # Validate parts
        if not customer_name or not expiry_date_str or not provided_signature:
            return (False, "Invalid license key: missing required components")
        
        # Step 2: Re-generate the signature locally
        payload = f"{customer_name}|{expiry_date_str}"
        
        calculated_signature = hmac.new(
            SECRET_SALT.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()[:16]  # Take first 16 characters
        
        # Step 3: Check 1 - Anti-tamper check (signature match)
        # Use hmac.compare_digest for timing-safe comparison
        if not hmac.compare_digest(calculated_signature, provided_signature):
            return (False, "Invalid license signature. License may be tampered or forged.")
        
        # Step 4: Check 2 - Expiration check
        try:
            # Parse expiry date (format: YYYYMMDD)
            expiry_date = datetime.strptime(expiry_date_str, "%Y%m%d")
            current_date = datetime.now()
            
            # Compare dates only (not time) - license expires at end of expiry day
            if current_date.date() > expiry_date.date():
                return (False, f"License has expired on {expiry_date.strftime('%Y-%m-%d')}")
        
        except ValueError:
            return (False, f"Invalid expiry date format in license key: {expiry_date_str}")
        
        # All checks passed!
        return (True, "License is valid")
    
    except Exception as e:
        return (False, f"License verification failed: {str(e)}")


# Convenience function for simple boolean check
def is_license_valid(key_string: str) -> bool:
    """
    Simple boolean check if license is valid.
    
    Args:
        key_string: License key to verify
        
    Returns:
        True if license is valid, False otherwise
    """
    is_valid, _ = verify_license_key(key_string)
    return is_valid
