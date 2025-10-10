from app import db, create_app
from app.models import Quiz

def add_subject_id_column():
    """Add subject_id column to quizzes table if it doesn't exist"""
    app = create_app()
    with app.app_context():
        # Check if the column exists
        try:
            # Try to query using subject_id to see if it exists
            Quiz.query.filter_by(subject_id=1).first()
            print("Column subject_id already exists in quizzes table")
        except Exception as e:
            if "no such column" in str(e):
                # Add the column
                db.engine.execute('ALTER TABLE quizzes ADD COLUMN subject_id INTEGER REFERENCES subjects(id)')
                print("Added subject_id column to quizzes table")
                # Set a default value for existing records
                db.engine.execute('UPDATE quizzes SET subject_id = 1 WHERE subject_id IS NULL')
                print("Set default subject_id=1 for existing records")
            else:
                print(f"Unexpected error: {e}")

if __name__ == "__main__":
    add_subject_id_column()