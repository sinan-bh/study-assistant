from app import db, create_app

app = create_app()

def add_description_column():
    with app.app_context():
        # Add the description column to the quizzes table
        db.engine.execute('ALTER TABLE quizzes ADD COLUMN description TEXT')
        print("Successfully added description column to quizzes table")

if __name__ == '__main__':
    add_description_column()