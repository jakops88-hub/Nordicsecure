# HMAC-Based Offline Licensing System for NordicSecure

## Overview

This is a complete, offline licensing system that uses HMAC-SHA256 cryptographic signatures to generate and validate license keys. The system consists of two main components:

1. **admin_keygen.py** (The Factory) - Admin tool for generating license keys and managing customer database
2. **backend/license_validator.py** (The Lock) - Module for validating license keys in the application

## Features

- ✅ **100% Offline** - No external connections required
- ✅ **Cryptographically Secure** - Uses HMAC-SHA256 for tamper-proof signatures
- ✅ **Lightweight CRM** - Customer database stored in CSV format
- ✅ **Easy Integration** - Simple API for license validation
- ✅ **Name Sanitization** - Handles special characters and spaces in customer names
- ✅ **Expiration Management** - Automatic expiration date validation

## License Key Format

```
CUSTOMERNAME-EXPIRYDATE-SIGNATURE
```

Example: `JOHNDOE-20260108-A1B2C3D4E5F6G7H8`

Where:
- **CUSTOMERNAME**: Sanitized customer name (uppercase, alphanumeric only)
- **EXPIRYDATE**: Expiration date in YYYYMMDD format
- **SIGNATURE**: First 16 characters of HMAC-SHA256 signature

## Installation

No additional dependencies required beyond Python 3 standard library.

## Usage

### For Administrators: Generating License Keys

Run the admin tool:

```bash
python3 admin_keygen.py
```

The tool will prompt you for:
- **Customer Name**: Full name of the customer
- **Customer Email**: Customer's email address
- **Company/Organization**: Customer's company name
- **Days Valid**: Number of days the license is valid (default: 365)

Example session:
```
======================================================================
NordicSecure License Key Generator
======================================================================

Customer Name: John Doe
Customer Email: john.doe@example.com
Company/Organization: Acme Corporation
Days Valid (default: 365): 30

✓ Created new database: customer_db.csv
✓ Customer record added to customer_db.csv

======================================================================
LICENSE KEY GENERATED
======================================================================

Customer:     John Doe
Email:        john.doe@example.com
Company:      Acme Corporation
Valid Until:  2026-02-06

LICENSE KEY:
----------------------------------------------------------------------
JOHNDOE-20260206-06053c4cfadb3f58
----------------------------------------------------------------------

Copy the license key above and send it to the customer via email.
======================================================================
```

### Customer Database

Customer details are automatically saved to `customer_db.csv` with the following fields:
- Created_Date
- Customer_Name
- Email
- Company
- License_Key
- Expiry_Date
- Status

**Note**: The `customer_db.csv` file is automatically excluded from git via `.gitignore` to protect customer data.

### For Developers: Validating License Keys

```python
from backend.license_validator import verify_license_key, is_license_valid

# Method 1: Get detailed validation result
key = "JOHNDOE-20260206-06053c4cfadb3f58"
is_valid, message = verify_license_key(key)

if is_valid:
    print(f"✓ {message}")
    # Grant access to application
else:
    print(f"✗ {message}")
    # Deny access to application

# Method 2: Simple boolean check
if is_license_valid(key):
    # Grant access
    pass
else:
    # Deny access
    pass
```

## Security Features

### Anti-Tamper Protection

The system uses HMAC-SHA256 to create a cryptographic signature of the license data. Any modification to the customer name or expiration date will invalidate the signature.

**Test Example:**
```python
# Valid key
verify_license_key("JOHNDOE-20260206-06053c4cfadb3f58")
# Returns: (True, "License is valid")

# Tampered key (modified signature)
verify_license_key("JOHNDOE-20260206-FFFFFFFFFFFFFFFF")
# Returns: (False, "Invalid license signature. License may be tampered or forged.")
```

### Expiration Validation

Keys automatically expire at midnight on the specified date.

**Test Example:**
```python
# Expired key
verify_license_key("JOHNDOE-20230101-validsiganture16")
# Returns: (False, "License has expired on 2023-01-01")
```

### Name Sanitization

Customer names are sanitized to prevent parsing errors:
- Removes all spaces and special characters
- Converts to uppercase
- Keeps only alphanumeric characters

**Examples:**
- "John Doe" → "JOHNDOE"
- "María José García-Pérez" → "MARAJOSGARCAPREZ"
- "O'Brien & Associates" → "OBRIENASSOCIATES"

## Validation Results

The `verify_license_key()` function returns a tuple of `(bool, str)`:

| Result | Message | Meaning |
|--------|---------|---------|
| `(True, "License is valid")` | License passed all checks | Grant access |
| `(False, "Invalid license key format...")` | Malformed key string | Deny access |
| `(False, "Invalid license signature...")` | Signature doesn't match | Deny access (tampered) |
| `(False, "License has expired on...")` | Date has passed | Deny access (expired) |

## Cryptography Details

### HMAC-SHA256

- **Algorithm**: HMAC (Hash-based Message Authentication Code) with SHA-256
- **Secret Salt**: Hardcoded in both scripts (keep this secret!)
- **Payload**: `CUSTOMERNAME|EXPIRYDATE`
- **Signature**: First 16 characters of the hex digest

### Why HMAC-SHA256?

- ✅ **Proven Security**: Industry-standard cryptographic algorithm
- ✅ **Tamper-Proof**: Any modification invalidates the signature
- ✅ **Fast Verification**: Millisecond-level performance
- ✅ **No External Dependencies**: Uses Python's standard library

## Testing

### Test Suite

Run comprehensive tests:

```bash
cd /home/runner/work/Nordicsecure/Nordicsecure

# Test key generation
python3 admin_keygen.py

# Test validator with various scenarios
python3 << 'EOF'
import sys
sys.path.insert(0, 'backend')
from license_validator import verify_license_key

# Test valid key
print("Valid key:", verify_license_key("JOHNDOE-20260206-06053c4cfadb3f58"))

# Test tampered signature
print("Tampered:", verify_license_key("JOHNDOE-20260206-FFFFFFFFFFFFFFFF"))

# Test expired key (create a properly signed but expired key for testing)
import hmac, hashlib
SECRET_SALT = "NordicSecure_2026_HMAC_Secret_Salt_DO_NOT_SHARE"
payload = "JOHNDOE|20230101"
sig = hmac.new(SECRET_SALT.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()[:16]
expired_key = f"JOHNDOE-20230101-{sig}"
print("Expired:", verify_license_key(expired_key))

# Test malformed key
print("Malformed:", verify_license_key("INVALID"))
EOF
```

## Integration with NordicSecure Application

### Example Integration

```python
from backend.license_validator import verify_license_key

def protected_feature():
    """Example of a protected feature that requires a valid license."""
    # Get license key from config, environment, or user input
    license_key = get_license_key_from_config()
    
    # Validate license
    is_valid, message = verify_license_key(license_key)
    
    if not is_valid:
        print(f"License validation failed: {message}")
        return False
    
    # License is valid, proceed with feature
    print("License is valid. Accessing protected feature...")
    # ... feature code here ...
    return True
```

### Middleware Integration

For FastAPI or Flask applications, you can create middleware to protect endpoints:

```python
from fastapi import HTTPException, Request
from backend.license_validator import verify_license_key

async def license_middleware(request: Request):
    """Middleware to validate license for protected endpoints."""
    license_key = os.getenv("NORDIC_LICENSE") or read_license_from_file()
    
    if not license_key:
        raise HTTPException(status_code=403, detail="License not found")
    
    is_valid, message = verify_license_key(license_key)
    if not is_valid:
        raise HTTPException(status_code=403, detail=message)
```

## Important Security Notes

1. **Keep SECRET_SALT Secret**: The `SECRET_SALT` in both scripts must be kept confidential. Anyone with access to this salt can generate valid license keys.

2. **Protect customer_db.csv**: This file contains sensitive customer information and should never be committed to version control or shared publicly.

3. **Secure Key Distribution**: License keys should be distributed to customers via secure channels (encrypted email, secure portal, etc.).

4. **Regular Rotation**: Consider rotating the `SECRET_SALT` periodically and regenerating customer keys.

## Troubleshooting

### Issue: "License not found"

**Solution**: Ensure the license key is properly provided to the application.

### Issue: "Invalid license signature"

**Possible Causes**:
- License key was manually modified
- Wrong SECRET_SALT in validator
- Key was corrupted during copy/paste

**Solution**: Generate a new license key using admin_keygen.py

### Issue: "License has expired"

**Solution**: Generate a new license key with a future expiration date.

### Issue: Special characters in customer name

**Not an Issue**: The system automatically sanitizes names to remove special characters. This is by design to prevent parsing errors.

## License System Comparison

This HMAC-based system coexists with the existing Ed25519-based system in the repository:

| Feature | HMAC System (This) | Ed25519 System (Existing) |
|---------|-------------------|---------------------------|
| Location | `admin_keygen.py` + `backend/license_validator.py` | `tools/generate_license.py` + `backend/app/license_manager.py` |
| Algorithm | HMAC-SHA256 | Ed25519 Digital Signatures |
| Key Format | NAME-DATE-SIG | Base64 JSON |
| Database | CSV | None |
| Dependencies | None (stdlib) | cryptography library |
| Use Case | Lightweight CRM + Licensing | Pure Licensing |

Both systems are independent and can be used for different purposes.

## Support

For questions or issues:
1. Check that the SECRET_SALT matches in both files
2. Verify the license key format is correct
3. Test with the provided test scripts
4. Review the validation error messages for details

---

**Created**: 2026-01-07  
**Version**: 1.0  
**Status**: Production Ready
