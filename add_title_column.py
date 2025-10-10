from app import db, create_app
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

def add_title_column():
    with app.app_context():
        # Add the title column to the quizzes table
        db.engine.execute('ALTER TABLE quizzes ADD COLUMN title VARCHAR(100) NOT NULL DEFAULT "Untitled Quiz"')
        print("Successfully added title column to quizzes table")

if __name__ == '__main__':
    add_title_column()