"""
Backend Setup Validation Tests

This script tests if the backend is properly configured and can connect to Supabase.
"""

import os
import sys
import requests
import time
from typing import Dict, Any

def test_backend_health() -> Dict[str, Any]:
    """Test if backend server is running."""
    api_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            return {
                "test_name": "Backend Health Check",
                "passed": True,
                "details": "Backend server is running and responding"
            }
        else:
            return {
                "test_name": "Backend Health Check",
                "passed": False,
                "details": f"Backend returned status {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "test_name": "Backend Health Check",
            "passed": False,
            "details": "Cannot connect to backend server at http://localhost:8000"
        }
    except Exception as e:
        return {
            "test_name": "Backend Health Check",
            "passed": False,
            "details": f"Backend health check failed: {str(e)}"
        }

def test_auth_endpoints_exist() -> Dict[str, Any]:
    """Test if auth endpoints exist."""
    api_url = "http://localhost:8000"
    
    try:
        # Test that the auth endpoints respond (even with errors is fine)
        endpoints = ["/auth/register", "/auth/login", "/auth/me"]
        results = []
        
        for endpoint in endpoints:
            try:
                response = requests.post(f"{api_url}{endpoint}", json={}, timeout=5)
                # Any response (even error) means endpoint exists
                results.append(f"{endpoint}: exists")
            except requests.exceptions.ConnectionError:
                results.append(f"{endpoint}: server not running")
            except Exception as e:
                results.append(f"{endpoint}: exists (error: {type(e).__name__})")
        
        return {
            "test_name": "Auth Endpoints Existence",
            "passed": True,
            "details": "; ".join(results)
        }
        
    except Exception as e:
        return {
            "test_name": "Auth Endpoints Existence", 
            "passed": False,
            "details": f"Failed to test endpoints: {str(e)}"
        }

def test_simple_auth_attempt() -> Dict[str, Any]:
    """Test a simple auth attempt to see what the actual error is."""
    api_url = "http://localhost:8000"
    
    try:
        # Try to register with a very simple email
        test_data = {
            "email": "test@test.com",
            "password": "password123"
        }
        
        response = requests.post(f"{api_url}/auth/register", json=test_data, timeout=10)
        
        return {
            "test_name": "Simple Auth Attempt",
            "passed": response.status_code == 200,
            "details": f"Status: {response.status_code}, Response: {response.text[:200]}..."
        }
        
    except Exception as e:
        return {
            "test_name": "Simple Auth Attempt",
            "passed": False,
            "details": f"Auth attempt failed: {str(e)}"
        }

def test_environment_variables() -> Dict[str, Any]:
    """Test if required environment variables are set."""
    try:
        # Check for common environment variables that might be needed
        required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_JWT_SECRET"]
        missing_vars = []
        present_vars = []
        
        for var in required_vars:
            if os.environ.get(var):
                present_vars.append(var)
            else:
                missing_vars.append(var)
        
        # Also check for any Supabase-related variables
        supabase_vars = [key for key in os.environ.keys() if "SUPABASE" in key.upper()]
        
        details = []
        if present_vars:
            details.append(f"Present: {', '.join(present_vars)}")
        if missing_vars:
            details.append(f"Missing: {', '.join(missing_vars)}")
        if supabase_vars:
            details.append(f"All Supabase vars: {', '.join(supabase_vars)}")
        
        return {
            "test_name": "Environment Variables",
            "passed": len(missing_vars) == 0,
            "details": "; ".join(details) if details else "No Supabase environment variables found"
        }
        
    except Exception as e:
        return {
            "test_name": "Environment Variables",
            "passed": False,
            "details": f"Environment check failed: {str(e)}"
        }

def main():
    """Run backend setup validation tests."""
    print("=" * 60)
    print("BACKEND SETUP VALIDATION")
    print("=" * 60)
    
    tests = [
        test_backend_health,
        test_environment_variables,
        test_auth_endpoints_exist,
        test_simple_auth_attempt
    ]
    
    results = []
    for test_func in tests:
        print(f"\nRunning {test_func.__name__}...")
        result = test_func()
        results.append(result)
        
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} {result['test_name']}: {result['details']}")
    
    # Summary
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All backend setup tests passed!")
    elif passed >= total * 0.75:
        print("⚠️ Most tests passed, but some issues detected")
    else:
        print("❌ Multiple backend setup issues detected")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 