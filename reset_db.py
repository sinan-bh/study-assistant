#!/usr/bin/env python3
"""
Database reset script for Study Assistant
Run this script to reset the database and recreate tables
"""

import os
from app import create_app, db
from app.models import User, Subject, Topic, StudySession, ExamMode

def reset_db():
    """Reset the database and recreate tables"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        print("✅ Database tables reset successfully!")
        
        # Create a sample user for testing
        sample_user = User(
            username='demo',
            email='demo@example.com',
            first_name='Demo',
            last_name='User'
        )
        sample_user.set_password('demo123')
        db.session.add(sample_user)
        db.session.commit()  # Commit user first to get the ID
        
        # Create sample subjects
        math_subject = Subject(
            name='Mathematics',
            description='Algebra, Geometry, Calculus',
            color='#007bff',
            daily_time_minutes=90,
            user_id=sample_user.id
        )
        db.session.add(math_subject)
        
        science_subject = Subject(
            name='Science',
            description='Physics, Chemistry, Biology',
            color='#28a745',
            daily_time_minutes=60,
            user_id=sample_user.id
        )
        db.session.add(science_subject)
        
        db.session.commit()
        
        print("✅ Sample data created successfully!")

if __name__ == '__main__':
    reset_db()