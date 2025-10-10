import sqlite3
import os

def create_quiz_tables():
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if quiz_questions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_questions'")
        if not cursor.fetchone():
            print("Creating quiz_questions table...")
            cursor.execute('''
                CREATE TABLE quiz_questions (
                    id INTEGER PRIMARY KEY,
                    quiz_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type VARCHAR(20) DEFAULT 'multiple_choice',
                    points INTEGER DEFAULT 1,
                    FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
                )
            ''')
            print("Successfully created quiz_questions table.")
        else:
            print("quiz_questions table already exists.")
            
        # Check if quiz_options table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_options'")
        if not cursor.fetchone():
            print("Creating quiz_options table...")
            cursor.execute('''
                CREATE TABLE quiz_options (
                    id INTEGER PRIMARY KEY,
                    question_id INTEGER NOT NULL,
                    option_text TEXT NOT NULL,
                    is_correct BOOLEAN DEFAULT 0,
                    FOREIGN KEY (question_id) REFERENCES quiz_questions (id) ON DELETE CASCADE
                )
            ''')
            print("Successfully created quiz_options table.")
        else:
            print("quiz_options table already exists.")
            
        # Check if quizzes table exists and update it if needed
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quizzes'")
        if not cursor.fetchone():
            print("Creating quizzes table...")
            cursor.execute('''
                CREATE TABLE quizzes (
                    id INTEGER PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    subject_id INTEGER,
                    created_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (subject_id) REFERENCES subjects (id)
                )
            ''')
            print("Successfully created quizzes table.")
        else:
            # Update the quizzes table to make subject_id nullable if needed
            cursor.execute("PRAGMA table_info(quizzes)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'subject_id' in columns:
                print("Checking subject_id constraint in quizzes table...")
                # Create a temporary table with proper foreign key constraint
                cursor.execute('''
                    CREATE TABLE quizzes_temp (
                        id INTEGER PRIMARY KEY,
                        title VARCHAR(100) NOT NULL,
                        description TEXT,
                        subject_id INTEGER,
                        created_at DATETIME,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (subject_id) REFERENCES subjects (id)
                    )
                ''')
                
                # Copy data
                cursor.execute('''
                    INSERT INTO quizzes_temp (id, title, description, subject_id, created_at, is_active)
                    SELECT id, title, description, subject_id, created_at, is_active FROM quizzes
                ''')
                
                # Drop old table
                cursor.execute("DROP TABLE quizzes")
                
                # Rename temp table
                cursor.execute("ALTER TABLE quizzes_temp RENAME TO quizzes")
                
                print("Successfully updated quizzes table with proper foreign key constraint.")
        
        conn.commit()
        print("All tables created/updated successfully.")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_quiz_tables()