import os
import sqlite3
import glob

def fix_database(db_path):
    """Fix the exam_modes table in the specified database."""
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False
        
    print(f"Fixing database at: {db_path}")
    
    # Connect directly to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if exam_modes table exists and drop it
    cursor.execute("DROP TABLE IF EXISTS exam_topics")
    cursor.execute("DROP TABLE IF EXISTS exam_modules")
    cursor.execute("DROP TABLE IF EXISTS exam_modes")
    
    print(f"Dropped existing tables in {db_path}")
    
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
    
    print(f"Fixed database tables in {db_path}")
    return True

# Get the base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Fix all possible database locations
db_paths = [
    os.path.join(base_dir, 'study_assistant.db'),
    os.path.join(base_dir, 'instance', 'study_assistant.db'),
    os.path.join(base_dir, 'instance', 'app.db'),
    os.path.join(base_dir, 'app.db')
]

# Also search for any .db files in the project
for db_file in glob.glob(os.path.join(base_dir, '**', '*.db'), recursive=True):
    if db_file not in db_paths:
        db_paths.append(db_file)

# Fix each database
fixed_count = 0
for db_path in db_paths:
    if fix_database(db_path):
        fixed_count += 1

print(f"Fixed {fixed_count} databases. The exam_modes table should now work correctly.")