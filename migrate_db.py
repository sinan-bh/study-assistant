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
            
            conn.commit()
            conn.close()
            print(f"Migration completed for {db_path}")
        else:
            print(f"Database not found at {db_path}")

if __name__ == "__main__":
    migrate_database()
    print("Database migration completed successfully.")