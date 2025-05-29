"""
Frontend Authentication Integration Validation Tests

This script tests the authentication flow and validates that all 
frontend components are properly integrated with the backend.
"""

import requests
import json
import time
from typing import Dict, Any, Optional


class FrontendAuthValidator:
    """Validates frontend authentication integration."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.auth_token: Optional[str] = None
        self.user_id: Optional[str] = None
        
    def test_auth_endpoints(self) -> Dict[str, Any]:
        """Test all authentication endpoints."""
        results = {
            "test_name": "Authentication Endpoints Validation",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": []
        }
        
        # Test 1: User Registration
        register_result = self._test_user_registration()
        results["tests"].append(register_result)
        
        if register_result["passed"]:
            # Test 2: User Login
            login_result = self._test_user_login()
            results["tests"].append(login_result)
            
            if login_result["passed"]:
                # Test 3: Protected Routes
                protected_result = self._test_protected_routes()
                results["tests"].append(protected_result)
                
                # Test 4: Token Validation
                token_result = self._test_token_validation()
                results["tests"].append(token_result)
                
                # Test 5: Logout
                logout_result = self._test_user_logout()
                results["tests"].append(logout_result)
        
        # Calculate overall success
        passed_tests = sum(1 for test in results["tests"] if test["passed"])
        total_tests = len(results["tests"])
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "overall_passed": passed_tests == total_tests
        }
        
        return results
    
    def _test_user_registration(self) -> Dict[str, Any]:
        """Test user registration endpoint."""
        test_result = {
            "test_name": "User Registration",
            "passed": False,
            "details": ""
        }
        
        try:
            # Generate unique test user with simpler email format
            timestamp = int(time.time())
            test_email = f"testuser{timestamp}@test.com"
            test_password = "TestPassword123!"
            
            registration_data = {
                "email": test_email,
                "password": test_password
            }
            
            response = self.session.post(
                f"{self.api_base_url}/auth/register",
                json=registration_data
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["access_token", "refresh_token", "user"]
                if all(field in data for field in required_fields):
                    self.auth_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    test_result["passed"] = True
                    test_result["details"] = f"Registration successful for {test_email}"
                else:
                    test_result["details"] = f"Missing required fields in response: {list(data.keys())}"
            else:
                # Try to get more detailed error info
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", response.text)
                except:
                    error_detail = response.text
                test_result["details"] = f"Registration failed with status {response.status_code}: {error_detail}"
                
        except Exception as e:
            test_result["details"] = f"Registration test failed with exception: {str(e)}"
            
        return test_result
    
    def _test_user_login(self) -> Dict[str, Any]:
        """Test user login endpoint."""
        test_result = {
            "test_name": "User Login",
            "passed": False,
            "details": ""
        }
        
        try:
            # Use the same credentials from registration
            if not self.auth_token:
                test_result["details"] = "Cannot test login - registration failed"
                return test_result
            
            # For this test, we'll create a new user and try to login
            timestamp = int(time.time())
            test_email = f"logintest{timestamp}@test.com"
            test_password = "LoginTestPassword123!"
            
            # Register first
            reg_response = self.session.post(
                f"{self.api_base_url}/auth/register",
                json={"email": test_email, "password": test_password}
            )
            
            if reg_response.status_code != 200:
                try:
                    error_data = reg_response.json()
                    error_detail = error_data.get("detail", reg_response.text)
                except:
                    error_detail = reg_response.text
                test_result["details"] = f"Failed to create test user for login test: {error_detail}"
                return test_result
            
            # Now test login
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            response = self.session.post(
                f"{self.api_base_url}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["access_token", "refresh_token", "user"]
                if all(field in data for field in required_fields):
                    # Update auth token for subsequent tests
                    self.auth_token = data["access_token"]
                    test_result["passed"] = True
                    test_result["details"] = f"Login successful for {test_email}"
                else:
                    test_result["details"] = f"Missing required fields in login response: {list(data.keys())}"
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", response.text)
                except:
                    error_detail = response.text
                test_result["details"] = f"Login failed with status {response.status_code}: {error_detail}"
                
        except Exception as e:
            test_result["details"] = f"Login test failed with exception: {str(e)}"
            
        return test_result
    
    def _test_protected_routes(self) -> Dict[str, Any]:
        """Test that protected routes require authentication."""
        test_result = {
            "test_name": "Protected Routes",
            "passed": False,
            "details": ""
        }
        
        try:
            if not self.auth_token:
                test_result["details"] = "Cannot test protected routes - no auth token"
                return test_result
            
            # Test accessing user profile (protected route)
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.get(
                f"{self.api_base_url}/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                if "id" in user_data and "email" in user_data:
                    test_result["passed"] = True
                    test_result["details"] = "Successfully accessed protected route with valid token"
                else:
                    test_result["details"] = f"Protected route returned invalid user data: {user_data}"
            else:
                test_result["details"] = f"Protected route failed with status {response.status_code}: {response.text}"
                
        except Exception as e:
            test_result["details"] = f"Protected routes test failed with exception: {str(e)}"
            
        return test_result
    
    def _test_token_validation(self) -> Dict[str, Any]:
        """Test token validation by trying with invalid token."""
        test_result = {
            "test_name": "Token Validation",
            "passed": False,
            "details": ""
        }
        
        try:
            # Test with invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            
            response = self.session.get(
                f"{self.api_base_url}/auth/me",
                headers=invalid_headers
            )
            
            # Should fail with 401 or 403
            if response.status_code in [401, 403]:
                test_result["passed"] = True
                test_result["details"] = "Invalid token correctly rejected"
            else:
                test_result["details"] = f"Invalid token not rejected - status: {response.status_code}"
                
        except Exception as e:
            test_result["details"] = f"Token validation test failed with exception: {str(e)}"
            
        return test_result
    
    def _test_user_logout(self) -> Dict[str, Any]:
        """Test user logout endpoint."""
        test_result = {
            "test_name": "User Logout",
            "passed": False,
            "details": ""
        }
        
        try:
            if not self.auth_token:
                test_result["details"] = "Cannot test logout - no auth token"
                return test_result
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.post(
                f"{self.api_base_url}/auth/logout",
                headers=headers
            )
            
            # Logout should succeed (status 200) or at least not error
            if response.status_code in [200, 204]:
                test_result["passed"] = True
                test_result["details"] = "Logout successful"
            else:
                test_result["details"] = f"Logout failed with status {response.status_code}: {response.text}"
                
        except Exception as e:
            test_result["details"] = f"Logout test failed with exception: {str(e)}"
            
        return test_result
    
    def test_session_integration(self) -> Dict[str, Any]:
        """Test that authenticated users can create and use sessions."""
        results = {
            "test_name": "Session Integration with Authentication",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": []
        }
        
        # First authenticate
        test_email = f"session_test_{int(time.time())}@example.com"
        test_password = "SessionTestPassword123!"
        
        # Register and login
        reg_response = self.session.post(
            f"{self.api_base_url}/auth/register",
            json={"email": test_email, "password": test_password}
        )
        
        session_test = {
            "test_name": "Authenticated Session Creation",
            "passed": False,
            "details": ""
        }
        
        try:
            if reg_response.status_code == 200:
                auth_data = reg_response.json()
                headers = {"Authorization": f"Bearer {auth_data['access_token']}"}
                
                # Try to create a session
                session_data = {
                    "job_role": "Software Engineer",
                    "job_description": "Python developer position",
                    "style": "formal",
                    "difficulty": "medium"
                }
                
                session_response = self.session.post(
                    f"{self.api_base_url}/api/session/create",
                    json=session_data,
                    headers=headers
                )
                
                if session_response.status_code == 200:
                    session_result = session_response.json()
                    if "session_id" in session_result:
                        session_test["passed"] = True
                        session_test["details"] = f"Successfully created session: {session_result['session_id']}"
                    else:
                        session_test["details"] = f"Session created but missing session_id: {session_result}"
                else:
                    session_test["details"] = f"Session creation failed: {session_response.status_code} - {session_response.text}"
            else:
                session_test["details"] = f"Failed to authenticate for session test: {reg_response.status_code}"
                
        except Exception as e:
            session_test["details"] = f"Session integration test failed: {str(e)}"
        
        results["tests"].append(session_test)
        
        # Calculate summary
        passed_tests = sum(1 for test in results["tests"] if test["passed"])
        total_tests = len(results["tests"])
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "overall_passed": passed_tests == total_tests
        }
        
        return results


def main():
    """Run all frontend authentication validation tests."""
    print("=" * 60)
    print("FRONTEND AUTHENTICATION VALIDATION")
    print("=" * 60)
    
    validator = FrontendAuthValidator()
    
    # Test 1: Authentication Endpoints
    print("\n1. Testing Authentication Endpoints...")
    auth_results = validator.test_auth_endpoints()
    
    print(f"\nAuthentication Results:")
    print(f"  Tests: {auth_results['summary']['passed_tests']}/{auth_results['summary']['total_tests']}")
    print(f"  Success Rate: {auth_results['summary']['success_rate']:.1f}%")
    
    for test in auth_results["tests"]:
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        print(f"  {status} {test['test_name']}: {test['details']}")
    
    # Test 2: Session Integration
    print("\n2. Testing Session Integration...")
    session_results = validator.test_session_integration()
    
    print(f"\nSession Integration Results:")
    print(f"  Tests: {session_results['summary']['passed_tests']}/{session_results['summary']['total_tests']}")
    print(f"  Success Rate: {session_results['summary']['success_rate']:.1f}%")
    
    for test in session_results["tests"]:
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        print(f"  {status} {test['test_name']}: {test['details']}")
    
    # Overall Summary
    total_tests = auth_results['summary']['total_tests'] + session_results['summary']['total_tests']
    total_passed = auth_results['summary']['passed_tests'] + session_results['summary']['passed_tests']
    overall_success = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "=" * 60)
    print("OVERALL VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_passed}/{total_tests}")
    print(f"Success Rate: {overall_success:.1f}%")
    
    if overall_success >= 95:
        print("🎉 VALIDATION SUCCESSFUL - Frontend authentication is ready!")
    elif overall_success >= 80:
        print("⚠️  PARTIAL SUCCESS - Some issues need attention")
    else:
        print("❌ VALIDATION FAILED - Multiple issues need to be resolved")
    
    print("=" * 60)


if __name__ == "__main__":
    main() 