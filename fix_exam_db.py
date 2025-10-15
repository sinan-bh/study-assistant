import os
import sqlite3
from app import create_app

app = create_app()
with app.app_context():
    # Get the database path from the app configuration
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')
    
    if not db_path:
        # If path is empty, use the default SQLite path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    print(f"Using database at: {db_path}")
    
    # Connect directly to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if exam_modes table exists and drop it
    cursor.execute("DROP TABLE IF EXISTS exam_topics")
    cursor.execute("DROP TABLE IF EXISTS exam_modules")
    cursor.execute("DROP TABLE IF EXISTS exam_modes")
    
    print("Dropped existing tables")
    
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create the exam_modules table
    cursor.execute('''
    CREATE TABLE exam_modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        module_number INTEGER NOT NULL,
        start_time DATETIME NOT NULL,
        revision_start_time DATETIME NOT NULL,
        revision_end_time DATETIME NOT NULL,
        is_completed BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (exam_id) REFERENCES exam_modes (id)
    )
    ''')
    
    # Create the exam_topics table
    cursor.execute('''
    CREATE TABLE exam_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id INTEGER NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        is_revised BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (module_id) REFERENCES exam_modules (id)
    )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database tables created successfully with correct schema.")