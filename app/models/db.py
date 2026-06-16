import sqlite3
import os

# Define the absolute path to the database file in the instance directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'database.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')

def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.
    Enables foreign keys and sets row_factory to sqlite3.Row.
    """
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys for this connection
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """
    Initializes the database using the schema.sql file.
    Creates tables and indexes if they do not exist.
    """
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
        
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        
    conn = get_db_connection()
    try:
        conn.executescript(schema_sql)
        
        # Dynamic migration check: add avatar column if it does not exist
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users);")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'avatar' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT '';")

        # Migration: add is_anonymous column to heart_transactions if missing
        cursor.execute("PRAGMA table_info(heart_transactions);")
        ht_columns = [row['name'] for row in cursor.fetchall()]
        if 'is_anonymous' not in ht_columns:
            cursor.execute("ALTER TABLE heart_transactions ADD COLUMN is_anonymous INTEGER DEFAULT 0;")
            
        conn.commit()
    finally:
        conn.close()
