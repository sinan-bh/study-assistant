from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# Model for blocked users chat feature
class AdminChat(db.Model):
    __tablename__ = 'admin_chats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_from_admin = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('user_chats', lazy='dynamic'))
    admin = db.relationship('User', foreign_keys=[admin_id], backref=db.backref('admin_chats', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AdminChat {self.id}>'

# Quiz models for admin functionality
class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    subject = db.relationship('Subject', backref=db.backref('quizzes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Quiz {self.title}>'

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')  # multiple_choice, true_false, short_answer
    points = db.Column(db.Integer, default=1)
    
    # Relationships
    options = db.relationship('QuizOption', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'

class QuizOption(db.Model):
    __tablename__ = 'quiz_options'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<QuizOption {self.id}>'

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    max_score = db.Column(db.Integer)
    
    # Relationships
    answers = db.relationship('QuizAnswer', backref='attempt', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<QuizAttempt {self.id}>'

class QuizAnswer(db.Model):
    __tablename__ = 'quiz_answers'
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('quiz_options.id'))
    text_answer = db.Column(db.Text)  # For short answer questions
    is_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<QuizAnswer {self.id}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
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
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # Hex color for UI
    daily_time_minutes = db.Column(db.Integer, default=60)  # Default 1 hour per day
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    start_hour = db.Column(db.Integer, default=8)
    start_minute = db.Column(db.Integer, default=0)
    end_hour = db.Column(db.Integer, default=9)
    end_minute = db.Column(db.Integer, default=0)
    # DateTime versions of start and end times
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    # Extra reminder scheduled time (UTC). When set, front-end will trigger reminder and then clear it
    extra_reminder_at = db.Column(db.DateTime)
    # Finished time (UTC) when user clicks Finish
    finished_at = db.Column(db.DateTime)
    
    @staticmethod
    def _create_datetime_from_hour_minute(hour, minute):
        """Create a datetime object from hour and minute values."""
        if hour is None or minute is None:
            return None
        try:
            # Create a datetime with today's date and the specified hour/minute
            now = datetime.utcnow()
            return datetime(now.year, now.month, now.day, int(hour), int(minute))
        except (ValueError, TypeError):
            return None
            
    def update_datetime_fields(self):
        """Update the datetime fields based on hour and minute values."""
        # Update start_time from start_hour and start_minute
        self.start_time = self._create_datetime_from_hour_minute(self.start_hour, self.start_minute)
        
        # Update end_time from end_hour and end_minute
        self.end_time = self._create_datetime_from_hour_minute(self.end_hour, self.end_minute)

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
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    estimated_time_minutes = db.Column(db.Integer, default=30)
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5 scale
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    study_sessions = db.relationship('StudySession', backref='topic', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Topic {self.name}>'

class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    actual_duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 scale for difficulty/understanding
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completion_status = db.Column(db.String(20))  # 'early', 'on_time', 'late', 'very_late'
    pass_status = db.Column(db.Boolean)  # True if passed, False if failed
    pass_percentage = db.Column(db.Integer)  # Percentage of success (0-100)

    def generate_recommendation(self, scheduled_end_time):
        """Generate recommendation based on completion time and set completion status."""
        now = datetime.utcnow()
        
        # Calculate time difference in minutes
        if self.end_time and scheduled_end_time:
            time_diff = (self.end_time - scheduled_end_time).total_seconds() / 60
            
            # Set completion status based on time difference
            if time_diff <= -10:  # Finished 10+ minutes early
                self.completion_status = 'early'
                message = "Great job! You finished early."
            elif time_diff <= 5:  # Finished on time or up to 5 minutes late
                self.completion_status = 'on_time'
                message = "Good job! You finished on time."
            elif time_diff <= 15:  # Finished 5-15 minutes late
                self.completion_status = 'late'
                message = "You finished a bit late. Try to manage your time better next time."
            else:  # Finished more than 15 minutes late
                self.completion_status = 'very_late'
                message = "You finished very late. Consider breaking down your study sessions into smaller chunks."
            
            # Set pass status based on time difference
            if time_diff <= 0:  # Only pass if finished before or exactly at scheduled time
                self.pass_status = True
                # Calculate how early they finished as a percentage (100% = right on time, >100% = early)
                time_ratio = max(0, 100 + min(100, (scheduled_end_time - self.end_time).total_seconds() / 60))
                self.pass_percentage = int(min(100, time_ratio))
                pass_message = f"You passed! Finished with {self.pass_percentage}% efficiency."
            else:
                self.pass_status = False
                # Calculate how late they finished as a percentage (0% = way too late, higher = closer to on time)
                time_ratio = max(0, 100 - min(100, (self.end_time - scheduled_end_time).total_seconds() / 60))
                self.pass_percentage = int(time_ratio)
                pass_message = f"You failed the subject. Completed {self.pass_percentage}% of the goal."
            
            return f"{message} {pass_message}"
        
        return "Session completed."
    
    def __repr__(self):
        return f'<StudySession {self.id}>'
        
    

class ExamMode(db.Model):
    __tablename__ = 'exam_modes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExamMode {self.id}>'

