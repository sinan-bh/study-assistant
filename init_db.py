#!/usr/bin/env python3
"""
Database initialization script for Study Assistant
Run this script to create the database and tables
"""

from app import create_app, db
from app.models import User, Subject, Topic, StudySession, ExamMode

def init_db():
    """Initialize the database with tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Create a sample user for testing (optional)
        if not User.query.first():
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
            
            db.session.commit()  # Commit subjects
            
            # Create sample topics
            algebra_topic = Topic(
                name='Algebra',
                description='Linear equations, quadratic equations',
                estimated_time_minutes=45,
                difficulty_level=3,
                subject_id=math_subject.id
            )
            db.session.add(algebra_topic)
            
            geometry_topic = Topic(
                name='Geometry',
                description='Triangles, circles, polygons',
                estimated_time_minutes=30,
                difficulty_level=2,
                subject_id=math_subject.id
            )
            db.session.add(geometry_topic)
            
            physics_topic = Topic(
                name='Physics',
                description='Mechanics, thermodynamics',
                estimated_time_minutes=60,
                difficulty_level=4,
                subject_id=science_subject.id
            )
            db.session.add(physics_topic)
            
            db.session.commit()
            
            print("✅ Sample data created!")
            print("📝 Demo user created:")
            print("   Username: demo")
            print("   Password: demo123")
            print("   Email: demo@example.com")
        else:
            print("ℹ️  Database already contains data, skipping sample data creation")

if __name__ == '__main__':
    init_db()
