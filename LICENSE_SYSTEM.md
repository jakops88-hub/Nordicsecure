# Nordic Secure License System

## Overview

Nordic Secure implements a 100% offline license verification system using Ed25519 asymmetric cryptography. This ensures that:
- Licenses are cryptographically signed and cannot be forged
- License verification happens entirely offline without any external connections
- Expired or invalid licenses are rejected before accessing protected endpoints

## Architecture

### Components

1. **License Manager** (`backend/app/license_manager.py`)
   - `LicenseVerifier` class that verifies licenses using Ed25519 public key
   - Reads licenses from environment variable or file
   - Validates signatures and expiration dates

2. **FastAPI Middleware** (`backend/main.py`)
   - Intercepts all API requests
   - Protected endpoints: `/search`, `/ingest`
   - Unprotected endpoints: `/`, `/health`
   - Returns 403 Forbidden for invalid/expired licenses

3. **License Generation Tool** (`tools/generate_license.py`)
   - Admin-only tool (not included in Docker containers)
   - Generates cryptographically signed licenses
   - Manages public/private keypairs

4. **Frontend Error Handling** (`frontend/app.py`)
   - Detects 403 license errors from backend
   - Displays prominent red alert box in Swedish

## License Format

Licenses are base64-encoded JSON objects containing:

```json
{
  "customer": "Customer Name",
  "expiration_date": "2025-12-31",
  "signature": "base64-encoded-ed25519-signature"
}
```

The signature is computed over the canonical JSON representation of `customer` and `expiration_date` fields.

## Usage

### For Administrators

#### 1. Generate Keypair (One-time)

```bash
cd tools
python generate_license.py generate-keypair
```

This generates:
- `private_key.txt` - Keep this secure! Never commit to git.
- `public_key.txt` - Copy this to `backend/app/license_manager.py`

#### 2. Generate License for Customer

```bash
python generate_license.py generate-license \
  --customer "Customer Name" \
  --expiration "2025-12-31"
```

This creates a license file: `license_customer_name_2025-12-31.key`

### For Customers

#### Option 1: Environment Variable

```bash
export NORDIC_LICENSE='<license_string>'
```

#### Option 2: License File

```bash
echo '<license_string>' > license.key
```

Place `license.key` in:
- Current working directory
- `/app/license.key` (in Docker container)

## API Behavior

### Protected Endpoints

| Endpoint | Without License | Expired License | Valid License |
|----------|----------------|-----------------|---------------|
| `/search` | 403 Forbidden | 403 Forbidden | Works |
| `/ingest` | 403 Forbidden | 403 Forbidden | Works |

### Unprotected Endpoints

| Endpoint | Always Available |
|----------|-----------------|
| `/` | Yes |
| `/health` | Yes |

### Error Response Format

```json
{
  "detail": "License Expired. Contact support to renew.",
  "error": "License expired on 2023-12-31. Contact support to renew."
}
```

## Security Features

1. **Asymmetric Cryptography**: Uses Ed25519 for signing
   - Private key never leaves admin's secure environment
   - Public key embedded in application cannot sign licenses

2. **Tamper-Proof**: Any modification to license data invalidates the signature

3. **Offline Verification**: No external connections required

4. **Time-Based Expiration**: Licenses automatically expire on specified date

5. **Minimal Attack Surface**: Simple, auditable codebase

## Testing

### Test License Verification

```bash
cd backend
python -c "
import sys
sys.path.insert(0, '.')
from app.license_manager import LicenseVerifier
verifier = LicenseVerifier()
result = verifier.check_license()
print('License valid:', result)
"
```

### Test API Endpoints

```bash
# Test without license
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
# Expected: 403 Forbidden

# Test with valid license
export NORDIC_LICENSE='<your_license>'
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
# Expected: Normal response (may fail on DB if not setup)
```

## Troubleshooting

### License Not Found

**Error**: `License not found. Please set NORDIC_LICENSE environment variable or create license.key file.`

**Solution**: Set the license using one of the methods above.

### License Expired

**Error**: `License Expired. Contact support to renew.`

**Solution**: Generate a new license with a future expiration date.

### Invalid Signature

**Error**: `Invalid license signature. License may be tampered with.`

**Solution**: The license has been modified. Request a new license from support.

### Frontend Shows Red Box

**Message**: "🔒 Din licens har gått ut. Kontakta Nordic Secure."

**Solution**: Contact Nordic Secure support to renew your license.

## Deployment

### Docker Deployment

1. Generate a license for the customer
2. Provide license as environment variable in `docker-compose.yml`:

```yaml
backend:
  environment:
    - NORDIC_LICENSE=<base64_license_string>
```

Or mount as a file:

```yaml
backend:
  volumes:
    - ./license.key:/app/license.key:ro
```

### Important Notes

- The `tools/` directory should NOT be included in Docker images
- Private keys should NEVER be committed to version control
- License files are automatically excluded by `.gitignore`

## Implementation Details

### Cryptography

- **Algorithm**: Ed25519 (Edwards-curve Digital Signature Algorithm)
- **Key Size**: 256 bits (32 bytes)
- **Signature Size**: 512 bits (64 bytes)
- **Library**: Python `cryptography` package

### Why Ed25519?

- Fast signature verification
- Small key and signature sizes
- High security level
- Well-tested and widely used
- No random number generation needed for signing

## Support

For license-related issues:
1. Check that license is not expired
2. Verify license string is correct (no extra spaces/newlines)
3. Check application logs for detailed error messages
4. Contact Nordic Secure support if issues persist
