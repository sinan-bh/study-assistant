import os
import sqlite3
from app import create_app

app = create_app()
with app.app_context():
    # Get the database path from the app configuration
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')
    
    print(f"Using database at: {db_path}")
    
    # Connect directly to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if exam_modes table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exam_modes'")
    if cursor.fetchone():
        print("Dropping existing exam_modes table")
        cursor.execute("DROP TABLE IF EXISTS exam_modes")
    
    # Create the exam_modes table with the correct schema
    cursor.execute('''
    CREATE TABLE exam_modes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name VARCHAR(100) NOT NULL,
        start_date DATETIME NOT NULL,
        end_date DATETIME NOT NULL,
        total_modules INTEGER DEFAULT 1,
        current_module INTEGER DEFAULT 1,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("Created exam_modes table with correct schema")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database fix completed successfully.")