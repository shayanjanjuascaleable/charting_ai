"""
SQLite database initialization script.
Creates tables matching the Azure SQL Server schema for seamless migration.
"""
import os
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_sqlite_schema(db_path: str = './backend/data/charting_ai.db'):
    """
    Initialize SQLite database with schema matching Azure SQL Server tables.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure data directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            Path(db_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created data directory: {db_dir}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create Account table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Account (
                AccountID INTEGER PRIMARY KEY,
                AccountName TEXT NULL,
                Region TEXT NULL,
                Industry TEXT NULL,
                Revenue NUMERIC NULL,
                CreatedDate TEXT NULL
            )
        """)
        logger.info("Created table: Account")
        
        # Create Contact table with foreign key
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Contact (
                ContactID INTEGER PRIMARY KEY,
                AccountID INTEGER NULL,
                FullName TEXT NULL,
                Role TEXT NULL,
                Email TEXT NULL,
                CreatedDate TEXT NULL,
                FOREIGN KEY(AccountID) REFERENCES Account(AccountID)
            )
        """)
        logger.info("Created table: Contact")
        
        # Create Lead table with foreign key
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Lead (
                LeadID INTEGER PRIMARY KEY,
                AccountID INTEGER NULL,
                LeadSource TEXT NULL,
                Status TEXT NULL,
                Budget NUMERIC NULL,
                CreatedDate TEXT NULL,
                FOREIGN KEY(AccountID) REFERENCES Account(AccountID)
            )
        """)
        logger.info("Created table: Lead")
        
        # Create Opportunity table with foreign key
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Opportunity (
                OpportunityID INTEGER PRIMARY KEY,
                AccountID INTEGER NULL,
                OpportunityName TEXT NULL,
                Stage TEXT NULL,
                Value NUMERIC NULL,
                ExpectedCloseDate TEXT NULL,
                FOREIGN KEY(AccountID) REFERENCES Account(AccountID)
            )
        """)
        logger.info("Created table: Opportunity")
        
        # Create indexes on AccountID foreign keys for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_Contact_AccountID 
            ON Contact(AccountID)
        """)
        logger.info("Created index: idx_Contact_AccountID")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_Lead_AccountID 
            ON Lead(AccountID)
        """)
        logger.info("Created index: idx_Lead_AccountID")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_Opportunity_AccountID 
            ON Opportunity(AccountID)
        """)
        logger.info("Created index: idx_Opportunity_AccountID")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"SQLite dataset schema initialized successfully at: {db_path}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error during initialization: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        return False


if __name__ == '__main__':
    # Get database path from environment or use default
    from backend.config import get_absolute_sqlite_path
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///./backend/data/charting_ai.db')
    
    # Use absolute path function (single source of truth)
    if database_url.startswith('sqlite:///'):
        db_path = get_absolute_sqlite_path(database_url)
    else:
        db_path = database_url
    
    success = init_sqlite_schema(db_path)
    
    if success:
        print("SQLite dataset schema initialized.")
    else:
        print("Failed to initialize SQLite schema. Check logs for details.")
        exit(1)

