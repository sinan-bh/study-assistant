import os
import sqlite3
from app import create_app, db
from app.models import ExamMode, ExamModule, ExamTopic

# Create the application context
app = create_app()
with app.app_context():
    # Get the database path
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    if not db_path:
        # If path is empty, use the default SQLite path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'study_assistant.db')
    
    print(f"Using database at: {db_path}")
    
    # Create the directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    # Use SQLAlchemy to create all tables
    db.create_all()
    print("Database tables created successfully using SQLAlchemy.")