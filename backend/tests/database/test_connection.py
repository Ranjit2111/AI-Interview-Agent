"""
Tests for the database connection module.
"""

import pytest
import sqlite3
from unittest.mock import MagicMock, patch
from pathlib import Path

from backend.database.connection import DatabaseConnection


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test.db"


@pytest.fixture
def db_connection(db_path):
    """Create a database connection instance for testing."""
    return DatabaseConnection(db_path)


class TestDatabaseConnection:
    """Tests for the DatabaseConnection class."""
    
    def test_initialization(self, db_connection, db_path):
        """Test that database connection initializes properly."""
        assert db_connection.db_path == db_path
        assert db_connection.connection is None
    
    def test_connect(self, db_connection):
        """Test database connection."""
        # Connect to database
        db_connection.connect()
        
        # Verify connection is established
        assert db_connection.connection is not None
        assert isinstance(db_connection.connection, sqlite3.Connection)
        
        # Test connection is working
        cursor = db_connection.connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
    
    def test_disconnect(self, db_connection):
        """Test database disconnection."""
        # Connect and then disconnect
        db_connection.connect()
        db_connection.disconnect()
        
        # Verify connection is closed
        assert db_connection.connection is None
    
    def test_execute_query(self, db_connection):
        """Test executing a query."""
        # Connect to database
        db_connection.connect()
        
        # Create a test table
        db_connection.execute_query("""
            CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Insert test data
        db_connection.execute_query(
            "INSERT INTO test (id, name) VALUES (?, ?)",
            (1, "test_name")
        )
        
        # Query the data
        result = db_connection.execute_query("SELECT * FROM test")
        assert len(result) == 1
        assert result[0][0] == 1
        assert result[0][1] == "test_name"
    
    def test_execute_many(self, db_connection):
        """Test executing multiple queries."""
        # Connect to database
        db_connection.connect()
        
        # Create a test table
        db_connection.execute_query("""
            CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Insert multiple rows
        data = [(1, "name1"), (2, "name2"), (3, "name3")]
        db_connection.execute_many(
            "INSERT INTO test (id, name) VALUES (?, ?)",
            data
        )
        
        # Query all data
        result = db_connection.execute_query("SELECT * FROM test")
        assert len(result) == 3
        assert result[0][0] == 1
        assert result[1][0] == 2
        assert result[2][0] == 3
    
    def test_connection_context(self, db_connection):
        """Test using database connection as context manager."""
        with db_connection as conn:
            # Verify connection is established
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)
            
            # Test connection is working
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        
        # Verify connection is closed
        assert db_connection.connection is None
    
    def test_error_handling(self, db_connection):
        """Test error handling in database operations."""
        # Connect to database
        db_connection.connect()
        
        # Test invalid query
        with pytest.raises(sqlite3.Error):
            db_connection.execute_query("INVALID SQL")
        
        # Test invalid parameters
        with pytest.raises(sqlite3.Error):
            db_connection.execute_query("SELECT * FROM nonexistent_table")
    
    def test_commit_and_rollback(self, db_connection):
        """Test transaction management."""
        # Connect to database
        db_connection.connect()
        
        # Create a test table
        db_connection.execute_query("""
            CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        try:
            # Start a transaction
            db_connection.execute_query("BEGIN TRANSACTION")
            
            # Insert test data
            db_connection.execute_query(
                "INSERT INTO test (id, name) VALUES (?, ?)",
                (1, "test_name")
            )
            
            # Commit the transaction
            db_connection.execute_query("COMMIT")
            
            # Verify data was committed
            result = db_connection.execute_query("SELECT * FROM test")
            assert len(result) == 1
            
            # Start another transaction
            db_connection.execute_query("BEGIN TRANSACTION")
            
            # Insert more data
            db_connection.execute_query(
                "INSERT INTO test (id, name) VALUES (?, ?)",
                (2, "test_name2")
            )
            
            # Rollback the transaction
            db_connection.execute_query("ROLLBACK")
            
            # Verify data was rolled back
            result = db_connection.execute_query("SELECT * FROM test")
            assert len(result) == 1
            
        finally:
            # Clean up
            db_connection.execute_query("DROP TABLE test")


if __name__ == "__main__":
    pytest.main(["-v"]) 