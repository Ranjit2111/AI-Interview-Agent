#!/usr/bin/env python3
"""
Script to run authentication tests with mock authentication enabled.
This allows testing without setting up Supabase.
"""

import os
import sys
import subprocess

# Set environment variable for mock authentication
os.environ["USE_MOCK_AUTH"] = "true"
os.environ["LOG_LEVEL"] = "INFO"

def main():
    print("=" * 60)
    print("RUNNING TESTS WITH MOCK AUTHENTICATION")
    print("=" * 60)
    
    # Run backend setup validation
    print("\n1. Running Backend Setup Validation...")
    result1 = subprocess.run([sys.executable, "tests/test_backend_setup.py"], 
                           capture_output=False)
    
    if result1.returncode == 0:
        print("\n2. Running Frontend Authentication Validation...")
        result2 = subprocess.run([sys.executable, "tests/test_frontend_auth_validation.py"], 
                               capture_output=False)
        
        if result2.returncode == 0:
            print("\n🎉 All tests passed with mock authentication!")
        else:
            print("\n❌ Frontend auth tests failed")
    else:
        print("\n❌ Backend setup tests failed")
    
    print("\n" + "=" * 60)
    print("NOTE: This used mock authentication for development.")
    print("For production, set up Supabase and use real authentication.")
    print("See ENVIRONMENT_SETUP.md for instructions.")
    print("=" * 60)

if __name__ == "__main__":
    main() 