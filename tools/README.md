# License Management Tools

This directory contains administrative tools for managing Nordic Secure licenses.

**⚠️ IMPORTANT: These tools should NOT be included in Docker containers or deployed with the application.**

## generate_license.py

Tool for generating cryptographically signed licenses using Ed25519.

### Generate a New Keypair

First, generate a keypair (only needed once):

```bash
python generate_license.py generate-keypair
```

This will:
1. Generate a new Ed25519 private/public keypair
2. Save them to `private_key.txt` and `public_key.txt`
3. Display the keys in the terminal

**Important:**
- Keep `private_key.txt` secure and do NOT commit it to git
- Copy the public key to `backend/app/license_manager.py` (PUBLIC_KEY_B64 constant)

### Generate a License

Generate a license for a customer:

```bash
python generate_license.py generate-license --customer "Customer Name" --expiration "2025-12-31"
```

This will:
1. Use the private key from `private_key.txt` (or provide via `--private-key`)
2. Generate a signed license
3. Save it to a file like `license_customer_name_2025-12-31.key`

### Using a License

Customers can use the license in two ways:

1. **Environment variable:**
   ```bash
   export NORDIC_LICENSE='<license_string>'
   ```

2. **File:**
   ```bash
   echo '<license_string>' > license.key
   ```

The application will check for licenses in this order:
1. `NORDIC_LICENSE` environment variable
2. `license.key` file in the application directory

## Security Notes

- The private key must be kept absolutely secure
- Never commit private keys or license files to version control
- Only distribute licenses to paying customers
- Each license is cryptographically signed and cannot be forged
- Licenses are validated offline without any external connections
