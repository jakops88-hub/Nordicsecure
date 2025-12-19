#!/usr/bin/env python3
"""
License Generation Tool for Nordic Secure

This tool generates cryptographically signed licenses for customers.
It uses Ed25519 asymmetric cryptography for signing.

Usage:
    python generate_license.py --customer "Customer Name" --expiration "2025-12-31"
    python generate_license.py --generate-keypair
"""

import os
import sys
import json
import base64
import argparse
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def generate_keypair():
    """
    Generate a new Ed25519 keypair for license signing.
    
    Returns:
        Tuple of (private_key, public_key) as base64 strings
    """
    # Generate private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize keys to bytes
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    # Encode as base64
    private_b64 = base64.b64encode(private_bytes).decode('utf-8')
    public_b64 = base64.b64encode(public_bytes).decode('utf-8')
    
    return private_b64, public_b64


def generate_license(customer: str, expiration_date: str, private_key_b64: str) -> str:
    """
    Generate a signed license for a customer.
    
    Args:
        customer: Customer name
        expiration_date: Expiration date in YYYY-MM-DD format
        private_key_b64: Base64-encoded private key
        
    Returns:
        Base64-encoded license string
    """
    # Validate expiration date format
    try:
        datetime.fromisoformat(expiration_date)
    except ValueError:
        raise ValueError(f"Invalid date format: {expiration_date}. Use YYYY-MM-DD format.")
    
    # Load private key
    try:
        private_key_bytes = base64.b64decode(private_key_b64)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    except Exception as e:
        raise ValueError(f"Invalid private key: {e}")
    
    # Create license data
    license_data = {
        "customer": customer,
        "expiration_date": expiration_date
    }
    
    # Create canonical JSON representation
    data_bytes = json.dumps(license_data, sort_keys=True).encode('utf-8')
    
    # Sign the data
    signature = private_key.sign(data_bytes)
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    # Add signature to license data
    license_data["signature"] = signature_b64
    
    # Encode complete license as base64
    license_json = json.dumps(license_data).encode('utf-8')
    license_b64 = base64.b64encode(license_json).decode('utf-8')
    
    return license_b64


def save_keypair_to_file(private_key_b64: str, public_key_b64: str):
    """
    Save keypair to files for safekeeping.
    
    Args:
        private_key_b64: Base64-encoded private key
        public_key_b64: Base64-encoded public key
    """
    # Save private key (keep this secret!)
    with open("private_key.txt", "w") as f:
        f.write(private_key_b64)
    print("✓ Private key saved to: private_key.txt")
    print("  ⚠️  KEEP THIS FILE SECURE AND DO NOT COMMIT TO GIT!")
    
    # Save public key (this goes into the application)
    with open("public_key.txt", "w") as f:
        f.write(public_key_b64)
    print("✓ Public key saved to: public_key.txt")
    print("  → Copy this key to backend/app/license_manager.py PUBLIC_KEY_B64")


def main():
    parser = argparse.ArgumentParser(
        description="Generate cryptographically signed licenses for Nordic Secure"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Generate keypair command
    keypair_parser = subparsers.add_parser(
        "generate-keypair",
        help="Generate a new Ed25519 keypair for license signing"
    )
    
    # Generate license command
    license_parser = subparsers.add_parser(
        "generate-license",
        help="Generate a signed license for a customer"
    )
    license_parser.add_argument(
        "--customer",
        required=True,
        help="Customer name"
    )
    license_parser.add_argument(
        "--expiration",
        required=True,
        help="Expiration date (YYYY-MM-DD format)"
    )
    license_parser.add_argument(
        "--private-key",
        help="Base64-encoded private key (or will read from private_key.txt)"
    )
    
    args = parser.parse_args()
    
    if args.command == "generate-keypair":
        print("Generating new Ed25519 keypair...")
        private_key, public_key = generate_keypair()
        
        print("\n" + "="*70)
        print("KEYPAIR GENERATED")
        print("="*70)
        print("\nPrivate Key (KEEP SECRET!):")
        print(private_key)
        print("\nPublic Key (use in application):")
        print(public_key)
        print("\n" + "="*70)
        
        # Save to files
        print("\nSaving keys to files...")
        save_keypair_to_file(private_key, public_key)
        
    elif args.command == "generate-license":
        # Get private key
        private_key = args.private_key
        if not private_key:
            # Try to read from file
            if os.path.exists("private_key.txt"):
                with open("private_key.txt", "r") as f:
                    private_key = f.read().strip()
                print("Using private key from private_key.txt")
            else:
                print("Error: No private key provided and private_key.txt not found")
                print("Run 'generate-keypair' first or provide --private-key")
                sys.exit(1)
        
        print(f"Generating license for: {args.customer}")
        print(f"Expiration date: {args.expiration}")
        
        try:
            license_str = generate_license(
                customer=args.customer,
                expiration_date=args.expiration,
                private_key_b64=private_key
            )
            
            print("\n" + "="*70)
            print("LICENSE GENERATED")
            print("="*70)
            print("\nLicense String:")
            print(license_str)
            print("\n" + "="*70)
            print("\nTo use this license:")
            print("1. Set environment variable: export NORDIC_LICENSE='<license_string>'")
            print("2. Or save to file: echo '<license_string>' > license.key")
            print("\n" + "="*70)
            
            # Save to file
            license_filename = f"license_{args.customer.replace(' ', '_').lower()}_{args.expiration}.key"
            with open(license_filename, "w") as f:
                f.write(license_str)
            print(f"\n✓ License saved to: {license_filename}")
            
        except Exception as e:
            print(f"Error generating license: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
