import sqlite3
import os

def add_question_text_column():
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(quiz_questions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'question_text' not in columns:
            print("Adding question_text column to quiz_questions table...")
            # Add the question_text column
            cursor.execute("ALTER TABLE quiz_questions ADD COLUMN question_text TEXT NOT NULL DEFAULT 'Default Question'")
            conn.commit()
            print("Successfully added question_text column to quiz_questions table.")
        else:
            print("question_text column already exists in quiz_questions table.")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_question_text_column()