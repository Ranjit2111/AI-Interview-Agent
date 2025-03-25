"""
Database migration script for AI Interviewer Agent.

This script handles migration of the database schema for the AI Interviewer Agent,
specifically for addressing the SQLAlchemy reserved name conflicts.
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    """Get the database file path from environment or use default."""
    # Load environment variables
    load_dotenv()
    
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./interview_app.db")
    logger.info(f"Using database URL: {db_url}")
    
    # Only handle SQLite databases
    if not db_url.startswith("sqlite:///"):
        logger.error("Only SQLite databases are supported for automatic migration")
        return None
    
    # Extract the file path from the SQLite URL
    if db_url.startswith("sqlite:///./"):
        # Remove the sqlite:///. prefix for relative paths
        db_path = db_url.replace("sqlite:///./", "")
    elif db_url.startswith("sqlite:///"):
        # Handle absolute paths
        db_path = db_url.replace("sqlite:///", "")
        # On Windows, if it starts with /, it might be a drive letter path
        if os.name == 'nt' and db_path.startswith('/'):
            # Convert /C:/path to C:\path
            db_path = db_path[1:].replace('/', '\\')
    else:
        logger.error(f"Unsupported database URL format: {db_url}")
        sys.exit(1)
    
    # Ensure the directory exists
    db_file = Path(db_path)
    db_dir = db_file.parent
    if not db_dir.exists() and str(db_dir) != '.':
        logger.info(f"Creating directory: {db_dir}")
        db_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Database path: {db_file.resolve()}")
    return db_file

def check_columns_exist(conn, table, columns):
    """Check if columns exist in a table."""
    try:
        cursor = conn.cursor()
        for column in columns:
            cursor.execute(f"PRAGMA table_info({table})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            if column in column_names:
                return True
    except Exception as e:
        logger.error(f"Error checking columns: {e}")
    return False

def migrate_database():
    """Perform database migration."""
    db_path = get_db_path()
    if not db_path or not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    logger.info(f"Migrating database: {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Migrate questions table
        if check_columns_exist(conn, "questions", ["metadata"]):
            logger.info("Migrating 'questions' table...")
            cursor.execute("ALTER TABLE questions RENAME COLUMN metadata TO question_metadata")
        
        # Migrate resource_tracking table
        if check_columns_exist(conn, "resource_tracking", ["metadata"]):
            logger.info("Migrating 'resource_tracking' table...")
            cursor.execute("ALTER TABLE resource_tracking RENAME COLUMN metadata TO tracking_metadata")
        
        # Migrate transcripts table
        if check_columns_exist(conn, "transcripts", ["metadata"]):
            logger.info("Migrating 'transcripts' table...")
            cursor.execute("ALTER TABLE transcripts RENAME COLUMN metadata TO transcript_metadata")
        
        # Commit changes
        conn.execute("COMMIT")
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Rollback transaction on error
        try:
            conn.execute("ROLLBACK")
        except:
            pass
        return False
    finally:
        # Close connection
        if conn:
            conn.close()

def reset_database():
    """Remove the database file to force a clean start."""
    db_path = get_db_path()
    if not db_path:
        return False
    
    try:
        if db_path.exists():
            logger.warning(f"Removing database file: {db_path}")
            os.remove(db_path)
            logger.info("Database file removed. A new one will be created on next startup.")
            return True
    except Exception as e:
        logger.error(f"Failed to remove database: {e}")
    
    return False

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Database migration utility")
    parser.add_argument("--reset", action="store_true", help="Reset the database (delete it)")
    parser.add_argument("--migrate", action="store_true", help="Migrate the database schema")
    args = parser.parse_args()
    
    if args.reset:
        if reset_database():
            logger.info("Database reset successful")
        else:
            logger.error("Database reset failed")
            sys.exit(1)
    elif args.migrate:
        if migrate_database():
            logger.info("Database migration successful")
        else:
            logger.error("Database migration failed")
            sys.exit(1)
    else:
        parser.print_help() 