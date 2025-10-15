import sqlite3
import os

def migrate_database():
    """
    Add new columns to the database tables
    """
    # Get the database path - check both app directory and instance directory
    db_paths = [
        os.path.join('app', 'study_assistant.db'),
        os.path.join('instance', 'study_assistant.db')
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Migrating database at {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if study_sessions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_sessions'")
            if cursor.fetchone():
                # Check if columns already exist in study_sessions
                cursor.execute("PRAGMA table_info(study_sessions)")
                study_session_columns = [column[1] for column in cursor.fetchall()]
                
                # Add completion_status column if it doesn't exist
                if 'completion_status' not in study_session_columns:
                    cursor.execute("ALTER TABLE study_sessions ADD COLUMN completion_status VARCHAR(20)")
                    print("Added completion_status column to study_sessions")
                
                # Add recommendation column if it doesn't exist
                if 'recommendation' not in study_session_columns:
                    cursor.execute("ALTER TABLE study_sessions ADD COLUMN recommendation TEXT")
                    print("Added recommendation column to study_sessions")
                    
                # Add pass_status column if it doesn't exist
                if 'pass_status' not in study_session_columns:
                    cursor.execute("ALTER TABLE study_sessions ADD COLUMN pass_status BOOLEAN")
                    print("Added pass_status column to study_sessions")
                    
                # Add pass_percentage column if it doesn't exist
                if 'pass_percentage' not in study_session_columns:
                    cursor.execute("ALTER TABLE study_sessions ADD COLUMN pass_percentage INTEGER")
                    print("Added pass_percentage column to study_sessions")
            else:
                print("study_sessions table does not exist in this database, skipping")
            
            # Check if subjects table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
            if cursor.fetchone():
                # Check if columns already exist in subjects
                cursor.execute("PRAGMA table_info(subjects)")
                subject_columns = [column[1] for column in cursor.fetchall()]
                
                # Add start_time column if it doesn't exist
                if 'start_time' not in subject_columns:
                    cursor.execute("ALTER TABLE subjects ADD COLUMN start_time DATETIME")
                    print("Added start_time column to subjects")
                
                # Add end_time column if it doesn't exist
                if 'end_time' not in subject_columns:
                    cursor.execute("ALTER TABLE subjects ADD COLUMN end_time DATETIME")
                    print("Added end_time column to subjects")
                    
                # Add extra_reminder_at column if it doesn't exist
                if 'extra_reminder_at' not in subject_columns:
                    cursor.execute("ALTER TABLE subjects ADD COLUMN extra_reminder_at DATETIME")
                    print("Added extra_reminder_at column to subjects")
                    
                # Add finished_at column if it doesn't exist
                if 'finished_at' not in subject_columns:
                    cursor.execute("ALTER TABLE subjects ADD COLUMN finished_at DATETIME")
                    print("Added finished_at column to subjects")
            else:
                print("subjects table does not exist in this database, skipping")
            
            # Create quizzes table if it doesn't exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quizzes'")
            if not cursor.fetchone():
                cursor.execute('''
                CREATE TABLE quizzes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    subject_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (subject_id) REFERENCES subjects (id)
                )
                ''')
                print("Created quizzes table")
                
            # Create exam_modes table if it doesn't exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exam_modes'")
            if not cursor.fetchone():
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
                print("Created exam_modes table")
                
            # Create exam_modules table if it doesn't exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exam_modules'")
            if not cursor.fetchone():
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
                print("Created exam_modules table")
                
            # Create exam_topics table if it doesn't exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exam_topics'")
            if not cursor.fetchone():
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
                print("Created exam_topics table")
            
            # Create quiz_questions table if it doesn't exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_questions'")
            if not cursor.fetchone():
                cursor.execute('''
                CREATE TABLE quiz_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
                )
                ''')
                print("Created quiz_questions table")
            
            # Create quiz_options table if it doesn't exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_options'")
            if not cursor.fetchone():
                cursor.execute('''
                CREATE TABLE quiz_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    is_correct BOOLEAN NOT NULL DEFAULT 0,
                    FOREIGN KEY (question_id) REFERENCES quiz_questions (id)
                )
                ''')
                print("Created quiz_options table")
            
            conn.commit()
            conn.close()
            print(f"Migration completed for {db_path}")
        else:
            print(f"Database not found at {db_path}")

if __name__ == "__main__":
    migrate_database()
    print("Database migration completed successfully.")