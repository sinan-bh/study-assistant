from app import db, create_app
from app.models import Quiz

def add_is_active_column():
    """Add is_active column to quizzes table if it doesn't exist"""
    app = create_app()
    with app.app_context():
        # Check if the column exists
        try:
            # Try to query using is_active to see if it exists
            Quiz.query.filter_by(is_active=True).first()
            print("Column is_active already exists in quizzes table")
        except Exception as e:
            if "no such column" in str(e):
                # Add the column
                db.engine.execute('ALTER TABLE quizzes ADD COLUMN is_active BOOLEAN DEFAULT 1')
                print("Added is_active column to quizzes table")
                # Set a default value for existing records
                db.engine.execute('UPDATE quizzes SET is_active = 1 WHERE is_active IS NULL')
                print("Set default is_active=1 for existing records")
            else:
                print(f"Unexpected error: {e}")

if __name__ == "__main__":
    add_is_active_column()