from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    reminder_song_filename = db.Column(db.String(256))
    reminder_song_seconds = db.Column(db.Integer, default=10)
    # Lunch break settings
    break_duration_minutes = db.Column(db.Integer, default=30)
    lunch_break_until = db.Column(db.DateTime)
    
    # Relationships
    subjects = db.relationship('Subject', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # Hex color for UI
    daily_time_minutes = db.Column(db.Integer, default=60)  # Default 1 hour per day
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    start_hour = db.Column(db.Integer, default=8)
    start_minute = db.Column(db.Integer, default=0)
    end_hour = db.Column(db.Integer, default=9)
    end_minute = db.Column(db.Integer, default=0)
    # Extra reminder scheduled time (UTC). When set, front-end will trigger reminder and then clear it
    extra_reminder_at = db.Column(db.DateTime)
    # Finished time (UTC) when user clicks Finish
    finished_at = db.Column(db.DateTime)

    # Relationships
    topics = db.relationship('Topic', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Subject {self.name}>'

    @staticmethod
    def _format_ampm(hour: int, minute: int) -> str:
        """Return time in 12-hour format with AM/PM, zero-padded minutes."""
        try:
            h = int(hour) if hour is not None else 0
            m = int(minute) if minute is not None else 0
        except (TypeError, ValueError):
            h, m = 0, 0
        suffix = 'AM' if h < 12 else 'PM'
        h12 = h % 12
        if h12 == 0:
            h12 = 12
        return f"{h12:02d}:{m:02d} {suffix}"

    @property
    def start_time_ampm(self) -> str:
        return self._format_ampm(self.start_hour or 0, self.start_minute or 0)

    @property
    def end_time_ampm(self) -> str:
        return self._format_ampm(self.end_hour or 0, self.end_minute or 0)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    estimated_time_minutes = db.Column(db.Integer, default=30)
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5 scale
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    study_sessions = db.relationship('StudySession', backref='topic', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Topic {self.name}>'

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    actual_duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 scale for difficulty/understanding
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudySession {self.id}>'

class ExamMode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExamMode {self.id}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
