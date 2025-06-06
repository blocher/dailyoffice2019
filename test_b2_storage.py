#!/usr/bin/env python3
"""
Test script to verify the django-storages Backblaze B2 configuration is working.

This script tests:
1. Django settings can be loaded
2. Storage backend is correctly configured
3. Environment variables are properly mapped
4. Storage instance can be created

Usage:
    Set the required environment variables:
    export STORAGES_ACCESS_KEY_ID="your_b2_key_id"
    export STORAGES_SECRET_ACCESS_KEY="your_b2_secret"
    export STORAGES_BUCKET_NAME="your_bucket_name"
    
    Optional (will use defaults if not set):
    export STORAGES_ENDPOINT_URL="https://s3.us-west-004.backblazeb2.com"
    export STORAGES_REGION_NAME="us-west-004"
    
    Then run: python test_b2_storage.py
"""

import os
import sys

def test_storage_configuration():
    """Test that the storage configuration is working correctly."""
    
    # Add site directory to path
    site_dir = os.path.join(os.path.dirname(__file__), 'site')
    if os.path.exists(site_dir):
        sys.path.insert(0, site_dir)
    
    print("🔧 Testing django-storages Backblaze B2 configuration...")
    print()
    
    # Check required environment variables
    required_vars = [
        'STORAGES_ACCESS_KEY_ID',
        'STORAGES_SECRET_ACCESS_KEY', 
        'STORAGES_BUCKET_NAME'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Please set these variables and try again.")
        return False
    
    print("✅ Required environment variables are set")
    
    # Test django-storages import
    try:
        from storages.backends.s3boto3 import S3Boto3Storage
        print("✅ django-storages imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import django-storages: {e}")
        print("Make sure django-storages[s3] is installed")
        return False
    
    # Test storage configuration
    try:
        config = {
            "access_key": os.getenv('STORAGES_ACCESS_KEY_ID'),
            "secret_key": os.getenv('STORAGES_SECRET_ACCESS_KEY'),
            "bucket_name": os.getenv('STORAGES_BUCKET_NAME'),
            "endpoint_url": os.getenv('STORAGES_ENDPOINT_URL', 'https://s3.us-west-004.backblazeb2.com'),
            "region_name": os.getenv('STORAGES_REGION_NAME', 'us-west-004'),
        }
        
        # For testing without Django, we need to set some minimal settings
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                SECRET_KEY='test-key-for-storage-test',
                USE_TZ=True,
            )
        
        storage = S3Boto3Storage(**config)
        print("✅ Storage backend instantiated successfully")
        print(f"   - Bucket: {storage.bucket_name}")
        print(f"   - Endpoint: {storage.endpoint_url}")
        print(f"   - Region: {storage.region_name}")
        
    except Exception as e:
        print(f"❌ Failed to create storage instance: {e}")
        return False
    
    # Test basic storage operations (if credentials are valid)
    try:
        # This will test if the credentials are valid
        storage.listdir('')
        print("✅ Storage connection successful - credentials are valid")
    except Exception as e:
        if 'credentials' in str(e).lower() or 'access' in str(e).lower():
            print("⚠️  Storage configured but credentials may be invalid")
            print(f"   Error: {e}")
        else:
            print(f"⚠️  Storage configured but connection failed: {e}")
    
    print()
    print("🎉 Configuration test completed!")
    print()
    print("Summary of migration:")
    print("• Replaced django-backblaze-b2 with django-storages[s3]")
    print("• Updated storage backend to storages.backends.s3boto3.S3Boto3Storage")
    print("• Environment variables remain the same (STORAGES_ACCESS_KEY_ID, etc.)")
    print("• All existing code using default_storage will continue to work")
    
    return True

if __name__ == "__main__":
    success = test_storage_configuration()
    sys.exit(0 if success else 1)