#!/usr/bin/env python3
"""
Admin Key Generation Tool for NordicSecure
The Factory - Generates secure license keys and logs customer details
"""

import hmac
import hashlib
import csv
import os
from datetime import datetime, timedelta
import re

# Shared secret salt for HMAC signing (keep this secret!)
SECRET_SALT = "NordicSecure_2026_HMAC_Secret_Salt_DO_NOT_SHARE"


def sanitize_name(name):
    """
    Sanitize customer name for use in license key.
    Removes spaces and special characters, converts to uppercase.
    
    Args:
        name: Customer name to sanitize
        
    Returns:
        Sanitized name (uppercase, alphanumeric only)
    """
    # Remove all non-alphanumeric characters and convert to uppercase
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', name)
    return sanitized.upper()


def generate_license_key(customer_name, expiry_date):
    """
    Generate a secure license key using HMAC-SHA256.
    
    Args:
        customer_name: Customer name (will be sanitized)
        expiry_date: Expiry date in YYYYMMDD format
        
    Returns:
        License key in format: CUSTOMERNAME-EXPIRYDATE-SIGNATURE
    """
    # Sanitize customer name
    sanitized_name = sanitize_name(customer_name)
    
    # Create payload
    payload = f"{sanitized_name}|{expiry_date}"
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        SECRET_SALT.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()[:16]  # Take first 16 characters
    
    # Create final key
    license_key = f"{sanitized_name}-{expiry_date}-{signature}"
    
    return license_key


def ensure_csv_exists():
    """
    Ensure customer_db.csv exists with proper headers.
    Creates the file if it doesn't exist.
    """
    csv_file = "customer_db.csv"
    
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Created_Date",
                "Customer_Name",
                "Email",
                "Company",
                "License_Key",
                "Expiry_Date",
                "Status"
            ])
        print(f"✓ Created new database: {csv_file}")
    
    return csv_file


def add_customer_to_db(customer_name, email, company, license_key, expiry_date):
    """
    Add customer details to the CSV database.
    
    Args:
        customer_name: Customer name
        email: Customer email
        company: Company/Organization
        license_key: Generated license key
        expiry_date: Expiry date in YYYY-MM-DD format
    """
    csv_file = ensure_csv_exists()
    
    created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            created_date,
            customer_name,
            email,
            company,
            license_key,
            expiry_date,
            "Active"
        ])
    
    print(f"✓ Customer record added to {csv_file}")


def main():
    """
    Main function - prompts for customer details and generates license key.
    """
    print("=" * 70)
    print("NordicSecure License Key Generator")
    print("=" * 70)
    print()
    
    # Get customer details
    customer_name = input("Customer Name: ").strip()
    if not customer_name:
        print("Error: Customer name is required")
        return
    
    customer_email = input("Customer Email: ").strip()
    if not customer_email:
        print("Error: Customer email is required")
        return
    
    company = input("Company/Organization: ").strip()
    if not company:
        print("Error: Company/Organization is required")
        return
    
    days_valid_input = input("Days Valid (default: 365): ").strip()
    if days_valid_input:
        try:
            days_valid = int(days_valid_input)
        except ValueError:
            print("Error: Days Valid must be a number")
            return
    else:
        days_valid = 365
    
    # Calculate expiry date
    expiry_datetime = datetime.now() + timedelta(days=days_valid)
    expiry_date_formatted = expiry_datetime.strftime("%Y-%m-%d")  # For display and DB
    expiry_date_key = expiry_datetime.strftime("%Y%m%d")  # For key (compact format)
    
    # Generate license key
    license_key = generate_license_key(customer_name, expiry_date_key)
    
    # Add to database
    add_customer_to_db(
        customer_name,
        customer_email,
        company,
        license_key,
        expiry_date_formatted
    )
    
    # Display results
    print()
    print("=" * 70)
    print("LICENSE KEY GENERATED")
    print("=" * 70)
    print()
    print(f"Customer:     {customer_name}")
    print(f"Email:        {customer_email}")
    print(f"Company:      {company}")
    print(f"Valid Until:  {expiry_date_formatted}")
    print()
    print("LICENSE KEY:")
    print("-" * 70)
    print(license_key)
    print("-" * 70)
    print()
    print("Copy the license key above and send it to the customer via email.")
    print("=" * 70)


if __name__ == "__main__":
    main()
