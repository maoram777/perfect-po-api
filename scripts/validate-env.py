#!/usr/bin/env python3
"""
Environment Variable Validation Script
Checks for required environment variables before building Docker image.
Fails the build if any required configs are missing.
"""

import os
import sys
from typing import List, Dict

# Required environment variables for production deployment
REQUIRED_ENV_VARS = {
    'MONGODB_URI': 'MongoDB connection string (e.g., mongodb+srv://...)',
    'JWT_SECRET_KEY': 'JWT signing secret key',
    'KEEPA_API_KEY': 'Keepa API key for product enrichment',
    'AWS_ACCESS_KEY_ID': 'AWS access key ID',
    'AWS_SECRET_ACCESS_KEY': 'AWS secret access key',
}

# Optional environment variables with defaults
OPTIONAL_ENV_VARS = {
    'AWS_REGION': 'us-east-1',
    'ENVIRONMENT': 'dev',
    'DEBUG': 'false',
}

def validate_environment() -> bool:
    """Validate that all required environment variables are set."""
    print("🔍 Validating environment variables...")
    print("=" * 50)
    
    missing_vars = []
    validation_results = []
    
    # Check required variables
    print("\n📋 Required Environment Variables:")
    for var_name, description in REQUIRED_ENV_VARS.items():
        value = os.environ.get(var_name)
        if value:
            # Mask sensitive values
            if 'SECRET' in var_name or 'KEY' in var_name or 'PASSWORD' in var_name:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            
            print(f"  ✅ {var_name}: {display_value}")
            validation_results.append((var_name, True, value))
        else:
            print(f"  ❌ {var_name}: MISSING - {description}")
            missing_vars.append(var_name)
            validation_results.append((var_name, False, None))
    
    # Check optional variables
    print("\n📋 Optional Environment Variables:")
    for var_name, default_value in OPTIONAL_ENV_VARS.items():
        value = os.environ.get(var_name, default_value)
        print(f"  ℹ️  {var_name}: {value}")
    
    # Check for localhost fallbacks
    print("\n🚨 Security Checks:")
    mongodb_url = os.environ.get('MONGODB_URI', '')
    if 'localhost' in mongodb_url or '127.0.0.1' in mongodb_url:
        print(f"  ❌ MONGODB_URI contains localhost: {mongodb_url}")
        missing_vars.append('MONGODB_URI_LOCALHOST')
    else:
        print(f"  ✅ MONGODB_URI is remote (no localhost)")
    
    # Summary
    print("\n" + "=" * 50)
    if missing_vars:
        print(f"❌ Build Failed: {len(missing_vars)} required environment variables missing")
        print("\nMissing variables:")
        for var in missing_vars:
            if var in REQUIRED_ENV_VARS:
                print(f"  - {var}: {REQUIRED_ENV_VARS[var]}")
            elif var == 'MONGODB_URI_LOCALHOST':
                print(f"  - MONGODB_URI: Must be remote MongoDB, not localhost")
        
        print(f"\n💡 To fix this:")
        print(f"   1. Set the missing environment variables")
        print(f"   2. Ensure MONGODB_URI points to a remote MongoDB (not localhost)")
        print(f"   3. Re-run the build")
        return False
    else:
        print("✅ All required environment variables are set!")
        print("✅ MongoDB connection is remote (no localhost fallback)")
        print("✅ Build can proceed")
        return True

def main():
    """Main validation function."""
    print("🚀 Perfect PO API - Environment Validation")
    print("=" * 50)
    
    # Check if we're in a CI/CD environment
    ci_env = os.environ.get('CI', 'false').lower() == 'true'
    if ci_env:
        print("🔧 Running in CI/CD environment")
    else:
        print("💻 Running in local environment")
    
    # Validate environment
    is_valid = validate_environment()
    
    if not is_valid:
        print("\n❌ Environment validation failed!")
        sys.exit(1)
    
    print("\n🎉 Environment validation passed!")
    print("🚀 Docker build can proceed...")
    sys.exit(0)

if __name__ == "__main__":
    main()
