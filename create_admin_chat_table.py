import sqlite3
from app import create_app, db
from app.models import AdminChat

def create_admin_chat_table():
    app = create_app()
    with app.app_context():
        # Create the admin_chats table
        db.create_all()
        print("Admin chat table created successfully!")

if __name__ == "__main__":
    create_admin_chat_table()