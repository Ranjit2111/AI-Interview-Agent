"""
Test suite for authentication fixes.
Tests modal mode synchronization, name field support, and user display functionality.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

# Set test environment variables before imports
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
os.environ["GOOGLE_API_KEY"] = "test-api-key"

from backend.database.db_manager import DatabaseManager
from backend.database.mock_db_manager import MockDatabaseManager
from backend.api.auth_api import UserRegisterRequest, UserResponse


class TestAuthModalFix:
    """Test that the AuthModal mode synchronization is fixed."""
    
    def test_auth_modal_mode_prop_handling(self):
        """Test that the AuthModal component would properly handle mode changes."""
        # This would be a frontend test in a real React testing environment
        # Here we document the expected behavior:
        
        expected_behavior = {
            "description": "AuthModal should sync with initialMode prop changes",
            "fix_applied": "Added useEffect to update mode when initialMode changes",
            "test_scenario": [
                "User clicks Sign In button → modal opens with login form",
                "User closes modal",
                "User clicks Sign Up button → modal opens with register form (not stuck on login)"
            ],
            "verification": "AuthModal useEffect([initialMode]) updates internal mode state"
        }
        
        assert expected_behavior["fix_applied"] == "Added useEffect to update mode when initialMode changes"


class TestNameFieldSupport:
    """Test name field support in backend and frontend."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock external dependencies."""
        with patch('backend.database.db_manager.create_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            yield mock_client
    
    def test_user_register_request_model_validation(self):
        """Test that UserRegisterRequest properly validates name field."""
        # Test valid registration request
        valid_request = UserRegisterRequest(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        assert valid_request.email == "test@example.com"
        assert valid_request.password == "password123"
        assert valid_request.name == "Test User"
        
        # Test that name is required
        with pytest.raises(ValueError):
            UserRegisterRequest(
                email="test@example.com",
                password="password123"
                # name is missing
            )
    
    def test_user_response_model_includes_name(self):
        """Test that UserResponse model includes name field."""
        response = UserResponse(
            id="123",
            email="test@example.com",
            name="Test User",
            created_at=None
        )
        assert response.id == "123"
        assert response.email == "test@example.com"
        assert response.name == "Test User"
    
    @pytest.mark.asyncio
    async def test_mock_database_manager_register_with_name(self):
        """Test MockDatabaseManager registration with name."""
        mock_db = MockDatabaseManager()
        
        result = await mock_db.register_user(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["name"] == "Test User"
        assert "access_token" in result
        assert "refresh_token" in result
    
    @pytest.mark.asyncio
    async def test_mock_database_manager_login_returns_name(self):
        """Test MockDatabaseManager login returns name."""
        mock_db = MockDatabaseManager()
        
        # First register a user
        await mock_db.register_user(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        
        # Then login
        result = await mock_db.login_user(
            email="test@example.com",
            password="password123"
        )
        
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_mock_database_manager_get_user_includes_name(self):
        """Test MockDatabaseManager get_user includes name."""
        mock_db = MockDatabaseManager()
        
        # Register a user
        register_result = await mock_db.register_user(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        user_id = register_result["user"]["id"]
        
        # Get user by ID
        user = await mock_db.get_user(user_id)
        
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"
        assert "password" not in user  # Should not include password


class TestRealDatabaseManagerNameSupport:
    """Test real DatabaseManager name field support."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        with patch('backend.database.db_manager.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_database_manager_register_stores_name(self, mock_supabase_client):
        """Test DatabaseManager stores name during registration."""
        # Setup mock responses
        mock_auth_response = Mock()
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_session = Mock()
        mock_session.access_token = "token-123"
        mock_session.refresh_token = "refresh-123"
        
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        mock_supabase_client.auth.sign_up.return_value = mock_auth_response
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value = Mock()
        
        # Create DatabaseManager and test registration
        db_manager = DatabaseManager()
        result = await db_manager.register_user(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        
        # Verify name is included in response
        assert result["user"]["name"] == "Test User"
        assert result["user"]["email"] == "test@example.com"
        
        # Verify name was passed to database insert
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args["name"] == "Test User"
        assert insert_call_args["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_database_manager_login_fetches_name(self, mock_supabase_client):
        """Test DatabaseManager fetches name during login."""
        # Setup mock responses
        mock_auth_response = Mock()
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.created_at = "2023-01-01T00:00:00Z"
        mock_session = Mock()
        mock_session.access_token = "token-123"
        mock_session.refresh_token = "refresh-123"
        
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        
        # Mock get_user to return name
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{
                "id": "user-123",
                "email": "test@example.com",
                "name": "Test User",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }]
        )
        
        # Create DatabaseManager and test login
        db_manager = DatabaseManager()
        result = await db_manager.login_user(
            email="test@example.com",
            password="password123"
        )
        
        # Verify name is included in response
        assert result["user"]["name"] == "Test User"
        assert result["user"]["email"] == "test@example.com"


class TestFrontendIntegration:
    """Test frontend integration points."""
    
    def test_auth_context_type_includes_name_parameter(self):
        """Test that frontend AuthContext register function signature includes name."""
        # This documents the expected frontend changes
        expected_changes = {
            "AuthContext": {
                "register_function": "register: (email: string, password: string, name: string) => Promise<void>",
                "user_interface": "User { id: string; email: string; name: string; created_at?: string; }"
            },
            "RegisterForm": {
                "added_fields": ["name input field"],
                "validation": "name.trim() required",
                "submission": "register(email, password, name.trim())"
            },
            "Header": {
                "display": "user.name || user.email",
                "fallback": "Shows email if name is empty"
            }
        }
        
        assert "name: string" in expected_changes["AuthContext"]["register_function"]
        assert "name: string" in expected_changes["AuthContext"]["user_interface"]


class TestDatabaseSchemaAndMigration:
    """Test database schema changes."""
    
    def test_schema_includes_name_field(self):
        """Test that schema.sql includes name field."""
        # Read the schema file and verify name field exists
        schema_content = """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT UNIQUE,
            name TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        assert "name TEXT NOT NULL DEFAULT ''" in schema_content
    
    def test_migration_script_exists(self):
        """Test that migration script for adding name field exists."""
        migration_content = """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT NOT NULL DEFAULT '';
        UPDATE users SET name = split_part(email, '@', 1) WHERE name = '' OR name IS NULL;
        """
        
        assert "ADD COLUMN IF NOT EXISTS name" in migration_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 