#!/usr/bin/env python
"""
Database Migration Script for AI Interviewer Agent

This script handles database migration for renamed columns (metadata → *_metadata) 
in SQLAlchemy models to fix the reserved attribute name conflict.

Usage:
  python migrate_db.py --migrate  # Migrate database columns
  python migrate_db.py --reset    # Reset database (delete file)
"""

import os
import sys
import sqlite3
import logging
from dotenv import load_dotenv
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db-migration")

def get_db_path():
    """Get the database file path from environment or use default."""
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment or use default
    db_url = os.getenv("DATABASE_URL", "sqlite:///./interview_app.db")
    
    # Extract file path from SQLite URL
    if db_url.startswith("sqlite:///"):
        path = db_url.replace("sqlite:///", "")
        # Handle relative paths starting with ./
        if path.startswith("./"):
            path = path[2:]
        # Handle Windows absolute paths
        elif os.name == 'nt' and not os.path.isabs(path) and ':' in path:
            # This might be a Windows drive letter path with forward slashes
            path = path.replace('/', '\\')
        return path
    else:
        logger.error(f"Unsupported database URL: {db_url}")
        sys.exit(1)

def check_columns_exist(conn, table, columns):
    """Check if specified columns exist in a table."""
    cursor = conn.cursor()
    try:
        # Get column information for the table
        cursor.execute(f"PRAGMA table_info({table})")
        table_columns = [col[1] for col in cursor.fetchall()]
        
        # Check if all specified columns exist
        return all(col in table_columns for col in columns)
    except sqlite3.Error as e:
        logger.error(f"Error checking columns in {table}: {e}")
        return False
    finally:
        cursor.close()

def migrate_database():
    """Migrate database schema to handle renamed metadata columns."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        logger.info(f"Database file not found at {db_path}. No migration needed.")
        return True
    
    logger.info(f"Starting migration for database at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # 1. Migrate Question table
        if check_columns_exist(conn, "questions", ["metadata"]):
            logger.info("Migrating 'metadata' to 'question_metadata' in questions table...")
            cursor.execute("ALTER TABLE questions RENAME COLUMN metadata TO question_metadata")
            logger.info("Successfully renamed column in questions table")
        else:
            logger.info("No metadata column found in questions table or it's already migrated")
        
        # 2. Migrate ResourceTracking table
        if check_columns_exist(conn, "resource_tracking", ["metadata"]):
            logger.info("Migrating 'metadata' to 'tracking_metadata' in resource_tracking table...")
            cursor.execute("ALTER TABLE resource_tracking RENAME COLUMN metadata TO tracking_metadata")
            logger.info("Successfully renamed column in resource_tracking table")
        else:
            logger.info("No metadata column found in resource_tracking table or it's already migrated")
        
        # 3. Migrate Transcript table
        if check_columns_exist(conn, "transcripts", ["metadata"]):
            logger.info("Migrating 'metadata' to 'transcript_metadata' in transcripts table...")
            cursor.execute("ALTER TABLE transcripts RENAME COLUMN metadata TO transcript_metadata")
            logger.info("Successfully renamed column in transcripts table")
        else:
            logger.info("No metadata column found in transcripts table or it's already migrated")
        
        # Commit the transaction
        conn.execute("COMMIT")
        logger.info("Database migration completed successfully")
        return True
        
    except sqlite3.Error as e:
        if conn:
            conn.execute("ROLLBACK")
        logger.error(f"Database migration failed: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def reset_database():
    """Reset the database by removing the file."""
    db_path = get_db_path()
    
    try:
        if os.path.exists(db_path):
            logger.warning(f"Removing database file at {db_path}...")
            os.remove(db_path)
            logger.info("Database file removed successfully")
            return True
        else:
            logger.info(f"No database file found at {db_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Database migration and reset tool")
    parser.add_argument("--migrate", action="store_true", help="Migrate the database schema")
    parser.add_argument("--reset", action="store_true", help="Reset the database (delete file)")
    
    args = parser.parse_args()
    
    if args.reset:
        success = reset_database()
    elif args.migrate:
        success = migrate_database()
    else:
        logger.error("No action specified. Use --migrate or --reset")
        parser.print_help()
        sys.exit(1)
    
    sys.exit(0 if success else 1) 