import sqlite3
import os

def fix_quiz_tables():
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop existing quiz tables to recreate them
        print("Dropping existing quiz tables...")
        cursor.execute("DROP TABLE IF EXISTS quiz_options")
        cursor.execute("DROP TABLE IF EXISTS quiz_questions")
        
        # Recreate quiz_questions table
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
        
        # Recreate quiz_options table
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
        
        conn.commit()
        print("All quiz tables recreated successfully.")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_quiz_tables()