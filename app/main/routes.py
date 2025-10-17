from flask import render_template, redirect, url_for, request, jsonify, send_from_directory, current_app, session, flash
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.models import User, Subject, StudySession, Topic, Quiz, QuizQuestion, QuizOption, AdminChat, ExamSubject, ExamModule, ExamTopic, ExamStudySession
import random
import os
from sqlalchemy import func, distinct
from datetime import datetime, timedelta

# Exam Mode route
@bp.route('/exam-mode')
@login_required
def exam_mode():
    # Load exam subjects with modules and topics for current user (server-rendered, no API)
    exam_subjects = ExamSubject.query.filter_by(user_id=current_user.id, is_active=True).all()

    def serialize_exam_topic(et: ExamTopic):
        return {
            'id': et.id,
            'name': et.name,
            'description': et.description,
            'is_completed': et.is_completed
        }

    def serialize_exam_module(em: ExamModule):
        return {
            'id': em.id,
            'module_number': em.module_number,
            'topics': [serialize_exam_topic(t) for t in em.topics.all()]
        }

    def serialize_exam_subject(es: ExamSubject):
        return {
            'id': es.id,
            'name': es.name,
            'start_date': es.start_date.isoformat() if es.start_date else None,
            'end_date': es.end_date.isoformat() if es.end_date else None,
            'total_modules': es.total_modules,
            'is_active': es.is_active,
            'modules': [serialize_exam_module(m) for m in es.modules.all()]
        }

    exam_subjects_payload = [serialize_exam_subject(es) for es in exam_subjects]

    return render_template('main/exam_mode.html', exam_subjects=exam_subjects_payload)

@bp.route('/create-exam-subject', methods=['POST'])
@login_required
def create_exam_subject():
    name = request.form.get('name')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d') if request.form.get('start_date') else None
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None
    total_modules = int(request.form.get('total_modules', 1))
    
    if not name:
        flash('Subject name is required', 'error')
        return redirect(url_for('main.exam_mode'))
    if not start_date or not end_date:
        flash('Start date and end date are required', 'error')
        return redirect(url_for('main.exam_mode'))
    if total_modules < 1:
        flash('Total modules must be at least 1', 'error')
        return redirect(url_for('main.exam_mode'))
    
    # Create exam subject
    es = ExamSubject(
        name=name,
        start_date=start_date,
        end_date=end_date,
        total_modules=total_modules,
        user_id=current_user.id,
        is_active=True
    )
    db.session.add(es)
    db.session.flush()  # Get the ID without committing
    
    # Create modules
    for i in range(1, total_modules + 1):
        em = ExamModule(
            module_number=i,
            exam_subject_id=es.id
        )
        db.session.add(em)
    
    db.session.commit()
    flash('Exam subject created successfully', 'success')
    return redirect(url_for('main.exam_mode'))

@bp.route('/delete-exam-subject/<int:subject_id>', methods=['POST', 'DELETE'])
@login_required
def delete_exam_subject_main(subject_id: int):
    subject = ExamSubject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    # If form POST, redirect; if DELETE (fetch), return JSON
    if request.method == 'POST':
        flash('Exam subject deleted successfully', 'success')
        return redirect(url_for('main.exam_mode'))
    return jsonify({'success': True})

# Get list of users with chat messages
@bp.route('/chat-users')
@login_required
def chat_users():
    if current_user.is_admin:
        # For admins, get all users who have chat messages
        users_with_chats = db.session.query(User).join(
            AdminChat, AdminChat.user_id == User.id
        ).group_by(User.id).all()
    else:
        # For regular users, only show their own chats
        users_with_chats = [current_user] if AdminChat.query.filter_by(user_id=current_user.id).first() else []
    
    return render_template('main/chat_users.html', users=users_with_chats)

# Admin chat route for blocked users
@bp.route('/admin-chat/<int:user_id>', methods=['GET', 'POST'])
def admin_chat(user_id):
    user = User.query.get_or_404(user_id)
    
    # Create session key for this specific user's chat
    session_key = f'last_message_user_{user_id}'
    
    # Set a flag to indicate we're in the chat view
    session['in_chat_view'] = True
    
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            # Store the message in session
            session[session_key] = message
            
            # Create a new chat message
            chat = AdminChat(
                user_id=user_id,
                admin_id=current_user.id if current_user.is_authenticated and current_user.is_admin else None,
                message=message,
                is_from_admin=current_user.is_authenticated and current_user.is_admin
            )
            db.session.add(chat)
            db.session.commit()
            flash('Message sent successfully', 'success')
            
            # Clear the session after successful send to prevent duplicate messages
            session.pop(session_key, None)
    elif request.method == 'GET':
        # Check if there's a stored message that wasn't sent (due to refresh)
        if session_key in session:
            last_message = session.get(session_key)
            if last_message:
                # Resend the last message
                is_admin_user = current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin
                chat = AdminChat(
                    user_id=user_id,
                    admin_id=current_user.id if is_admin_user else None,
                    message=last_message,
                    is_from_admin=is_admin_user
                )
                db.session.add(chat)
                db.session.commit()
                flash('Previous message resent successfully', 'info')
                
                # Clear the session after successful resend
                session.pop(session_key, None)
    
    # Get all chat messages for this user
    chats = AdminChat.query.filter_by(user_id=user_id).order_by(AdminChat.timestamp).all()
    
    # Get all users with chats for the sidebar
    if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin:
        users_with_chats = db.session.query(User).join(
            AdminChat, AdminChat.user_id == User.id
        ).group_by(User.id).all()
    else:
        users_with_chats = [current_user] if current_user.is_authenticated and AdminChat.query.filter_by(user_id=current_user.id).first() else []
    
    return render_template('main/admin_chat.html', user=user, chats=chats, users=users_with_chats)

# Quiz routes for users
@bp.route('/quizzes')
@login_required
def quizzes():
    # Redirect admin users to admin quizzes page
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return redirect(url_for('admin.quizzes'))
        
    # Get all active quizzes
    quizzes = Quiz.query.filter_by(is_active=True).all()
    return render_template('main/quizzes.html', title='Quizzes', quizzes=quizzes)

@bp.route('/quiz/<int:quiz_id>')
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get all questions for this quiz and randomize them
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
    if not questions:
        return render_template('main/quiz_empty.html', quiz=quiz)
    
    # Randomize questions
    random_questions = random.sample(questions, len(questions))
    
    # Store question IDs in session
    session['quiz_questions'] = [q.id for q in random_questions]
    session['current_question_index'] = 0
    session['quiz_id'] = quiz_id
    session['quiz_start_time'] = datetime.utcnow().timestamp()
    session['quiz_answers'] = []
    
    # Redirect to the first question
    return redirect(url_for('main.quiz_question', question_index=0))

@bp.route('/quiz/question/<int:question_index>')
@login_required
def quiz_question(question_index):
    # Check if quiz is in progress
    if 'quiz_questions' not in session:
        return redirect(url_for('main.quizzes'))
    
    # Get quiz and question information
    quiz_id = session.get('quiz_id')
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if question index is valid
    question_ids = session.get('quiz_questions', [])
    if question_index >= len(question_ids) or question_index < 0:
        return redirect(url_for('main.quizzes'))
    
    # Get the current question
    question_id = question_ids[question_index]
    question = QuizQuestion.query.get_or_404(question_id)
    
    # Get options for this question
    options = QuizOption.query.filter_by(question_id=question_id).all()
    
    # Calculate progress
    progress = int((question_index / len(question_ids)) * 100)
    
    return render_template(
        'main/quiz_question.html',
        quiz=quiz,
        question=question,
        options=options,
        question_index=question_index,
        total_questions=len(question_ids),
        progress=progress
    )

@bp.route('/quiz/submit/<int:question_index>', methods=['POST'])
@login_required
def submit_answer(question_index):
    # Check if quiz is in progress
    if 'quiz_questions' not in session:
        return redirect(url_for('main.quizzes'))
    
    # Get selected option
    option_id = request.form.get('option_id')
    if not option_id:
        return redirect(url_for('main.quiz_question', question_index=question_index))
    
    # Save answer
    quiz_answers = session.get('quiz_answers', [])
    quiz_answers.append({
        'question_id': session['quiz_questions'][question_index],
        'option_id': int(option_id),
        'timestamp': datetime.utcnow().timestamp()
    })
    session['quiz_answers'] = quiz_answers
    
    # Move to next question or finish quiz
    next_index = question_index + 1
    if next_index < len(session['quiz_questions']):
        return redirect(url_for('main.quiz_question', question_index=next_index))
    else:
        return redirect(url_for('main.quiz_results'))

@bp.route('/quiz/results')
@login_required
def quiz_results():
    # Check if quiz is completed
    if 'quiz_questions' not in session or 'quiz_answers' not in session:
        return redirect(url_for('main.quizzes'))
    
    quiz_id = session.get('quiz_id')
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Calculate results
    correct_answers = 0
    total_questions = len(session['quiz_questions'])
    
    results = []
    for answer in session['quiz_answers']:
        question_id = answer['question_id']
        option_id = answer['option_id']
        
        question = QuizQuestion.query.get(question_id)
        selected_option = QuizOption.query.get(option_id)
        
        # Find correct option
        correct_option = QuizOption.query.filter_by(question_id=question_id, is_correct=True).first()
        
        is_correct = selected_option.is_correct if selected_option else False
        if is_correct:
            correct_answers += 1
            
        results.append({
            'question': question,
            'selected_option': selected_option,
            'correct_option': correct_option,
            'is_correct': is_correct
        })
    
    # Calculate score
    score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
    
    # Clear session data
    session.pop('quiz_questions', None)
    session.pop('current_question_index', None)
    session.pop('quiz_id', None)
    session.pop('quiz_start_time', None)
    session.pop('quiz_answers', None)
    
    return render_template(
        'main/quiz_results.html',
        quiz=quiz,
        results=results,
        score=score,
        correct_answers=correct_answers,
        total_questions=total_questions
    )

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/index.html', title='Study Assistant')

@bp.route('/dashboard')
@login_required
def dashboard():
    # Redirect admin users to admin dashboard
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
        
    # Clear expired break lazily
    if current_user.lunch_break_until and current_user.lunch_break_until <= datetime.utcnow():
        current_user.lunch_break_until = None
        db.session.commit()

    today = datetime.today().date()
    # All active subjects for stats and pie chart
    subjects = Subject.query.filter(
        Subject.user_id == current_user.id,
        Subject.is_active == True
    ).all()

    # Only subjects created today for the activity list
    subjects_today = Subject.query.filter(
        Subject.user_id == current_user.id,
        Subject.is_active == True,
        func.date(Subject.created_at) == today
    ).all()
    recent_sessions = StudySession.query.filter_by(user_id=current_user.id)\
        .order_by(StudySession.start_time.desc()).limit(5).all()

    # Stats (restrict counts and duration to subjects created today)
    # Finished IDs (for frontend flags) still computed from all subjects finished today
    finished_subject_ids = [s.id for s in subjects if (s.finished_at and s.finished_at.date() == today)]

    active_subjects_count = len(subjects_today)
    completed_subjects_count = sum(1 for s in subjects_today if (s.finished_at and s.finished_at.date() == today))
    pending_subjects_count = max(active_subjects_count - completed_subjects_count, 0)

    # Today's Total Activity Time: sum durations for today's-created subjects only
    def minutes_between(start_h:int, start_m:int, end_h:int, end_m:int) -> int:
        return max((end_h * 60 + end_m) - (start_h * 60 + start_m), 0)
    total_scheduled_minutes = sum(
        minutes_between(s.start_hour or 0, s.start_minute or 0, s.end_hour or 0, s.end_minute or 0)
        for s in subjects_today
    )

    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute

    # Subjects finished today (used to suppress end-time ringtone)
    # Use Subject.finished_at rather than sessions now
    # finished_subject_ids already computed above

    # Format today's date for display
    today_date = today.strftime('%A, %B %d, %Y')
    
    return render_template('main/dashboard.html', 
                         title='Dashboard',
                         subjects=subjects,
                         subjects_today=subjects_today,
                         recent_sessions=recent_sessions,
                         total_scheduled_minutes=total_scheduled_minutes,
                         active_subjects_count=active_subjects_count,
                         completed_subjects_count=completed_subjects_count,
                         pending_subjects_count=pending_subjects_count,
                         current_hour=current_hour,
                         current_minute=current_minute,
                         finished_subject_ids=finished_subject_ids,
                         is_on_break=bool(current_user.lunch_break_until and current_user.lunch_break_until > datetime.utcnow()),
                         break_remaining_seconds=max(int((current_user.lunch_break_until - datetime.utcnow()).total_seconds()), 0) if current_user.lunch_break_until else 0,
                         break_duration_minutes=current_user.break_duration_minutes or 30,
                         today_date=today_date)

@bp.route('/profile')
@login_required
def profile():
    return render_template('main/profile.html', title='Profile')

@bp.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html', title='Settings')

## Removed broken create_task route (used undefined fields and missing template)

@bp.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    data = request.get_json(silent=True) or {}
    sub_name = data.get('name')

    # Block adding subjects while on break
    if current_user.lunch_break_until and current_user.lunch_break_until > datetime.utcnow():
        return jsonify({'success': False, 'error': 'on_break'}), 423

    def parse_24_from_12(h12_val, ampm_val):
        try:
            h12 = int(h12_val)
        except (TypeError, ValueError):
            return None
        ampm = (ampm_val or '').strip().upper()
        if ampm not in ('AM', 'PM'):
            return None
        if ampm == 'AM':
            return h12 % 12
        return (h12 % 12) + 12

    # Prefer explicit 12-hour inputs if provided; fallback to 24-hour fields
    start_hour_12 = data.get('start_hour_12')
    start_ampm = data.get('start_ampm')
    end_hour_12 = data.get('end_hour_12')
    end_ampm = data.get('end_ampm')

    sh24_from_12 = parse_24_from_12(start_hour_12, start_ampm)
    eh24_from_12 = parse_24_from_12(end_hour_12, end_ampm)

    try:
        start_hour = int(data.get('start_hour')) if sh24_from_12 is None else int(sh24_from_12)
    except (TypeError, ValueError):
        start_hour = 8
    try:
        start_minute = int(data.get('start_minute', 0))
    except (TypeError, ValueError):
        start_minute = 0
    try:
        end_hour = int(data.get('end_hour')) if eh24_from_12 is None else int(eh24_from_12)
    except (TypeError, ValueError):
        end_hour = 9
    try:
        end_minute = int(data.get('end_minute', 0))
    except (TypeError, ValueError):
        end_minute = 0

    if not sub_name:
        return jsonify({'success': False, 'error': 'Missing fields'}), 400

    new_subject = Subject(
        name=sub_name,
        start_hour=start_hour,
        start_minute=start_minute,
        end_hour=end_hour,
        end_minute=end_minute,
        user_id=current_user.id,
        is_active=True
    )
    # Update datetime fields based on hour and minute values
    new_subject.update_datetime_fields()
    
    try:
        db.session.add(new_subject)
        db.session.commit()
        return jsonify({'success': True, 'subject': {'id': new_subject.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/subject/<int:subject_id>')
@login_required
def subject_detail(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    topics = Topic.query.filter_by(subject_id=subject.id, is_active=True).all()
    return render_template('main/subject_detail.html', subject=subject, topics=topics)

@bp.route('/subject/<int:subject_id>/add_topic', methods=['POST'])
@login_required
def add_topic(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'error': 'Missing topic name'}), 400
    topic = Topic(name=name, subject_id=subject.id, is_active=True)
    try:
        db.session.add(topic)
        db.session.commit()
        return jsonify({'success': True, 'topic': {'id': topic.id, 'name': topic.name}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/topic/<int:topic_id>/edit', methods=['POST'])
@login_required
def edit_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first()
    if not topic or topic.subject.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Topic not found'}), 404
    data = request.get_json() or {}
    new_name = (data.get('name') or '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'Missing topic name'}), 400
    topic.name = new_name
    db.session.commit()
    return jsonify({'success': True, 'topic': {'id': topic.id, 'name': topic.name}})

@bp.route('/subject/<int:subject_id>/edit', methods=['POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    subject.name = data.get('name', subject.name)
    
    # Update hour and minute fields if provided
    if 'start_hour' in data:
        subject.start_hour = data.get('start_hour')
    if 'start_minute' in data:
        subject.start_minute = data.get('start_minute')
    if 'end_hour' in data:
        subject.end_hour = data.get('end_hour')
    if 'end_minute' in data:
        subject.end_minute = data.get('end_minute')
    
    # Update datetime fields based on hour and minute values
    subject.update_datetime_fields()
    
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/settings/upload_reminder_song', methods=['POST'])
@login_required
def upload_reminder_song():
    play_seconds = request.form.get('play_seconds', type=int)
    if play_seconds is None or play_seconds < 1 or play_seconds > 60:
        play_seconds = 10  # default

    if 'reminder_song' in request.files and request.files['reminder_song'].filename != '':
        file = request.files['reminder_song']
        if not file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.aac')):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        upload_folder = os.path.join(current_app.root_path, 'static', 'reminder_songs')
        os.makedirs(upload_folder, exist_ok=True)
        filename = f"user_{current_user.id}_{file.filename}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        current_user.reminder_song_filename = filename

    current_user.reminder_song_seconds = play_seconds
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/settings/reminder_song')
@login_required
def get_reminder_song():
    if not current_user.reminder_song_filename:
        return '', 404
    upload_folder = os.path.join(current_app.root_path, 'static', 'reminder_songs')
    return send_from_directory(upload_folder, current_user.reminder_song_filename)

@bp.route('/settings/break', methods=['POST'])
@login_required
def set_break_duration():
    data = request.get_json(silent=True) or {}
    minutes = data.get('break_duration_minutes')
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        minutes = None
    if minutes is None or minutes not in (15, 20, 25, 30, 45, 60, 90):
        return jsonify({'success': False, 'error': 'invalid_minutes'}), 400
    current_user.break_duration_minutes = minutes
    db.session.commit()
    return jsonify({'success': True, 'break_duration_minutes': minutes})

@bp.route('/break/toggle', methods=['POST'])
@login_required
def toggle_break():
    data = request.get_json(silent=True) or {}
    turn_on = data.get('on')
    now = datetime.utcnow()
    if bool(turn_on):
        minutes = current_user.break_duration_minutes or 30
        current_user.lunch_break_until = now + timedelta(minutes=minutes)
    else:
        current_user.lunch_break_until = None
    db.session.commit()
    return jsonify({
        'success': True,
        'is_on_break': bool(current_user.lunch_break_until and current_user.lunch_break_until > datetime.utcnow()),
        'until': current_user.lunch_break_until.isoformat() + 'Z' if current_user.lunch_break_until else None
    })


@bp.route('/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
    if not subject:
        return jsonify({'success': False, 'error': 'Subject not found'}), 404
    # Proactively delete dependents to avoid FK issues (e.g., ExamMode)
    try:
        # Delete dependents
        StudySession.query.filter_by(user_id=current_user.id, subject_id=subject.id).delete(synchronize_session=False)
        # Topics will be deleted by cascade (delete-orphan). Explicit delete to be safe.
        Topic.query.filter_by(subject_id=subject.id).delete(synchronize_session=False)
        db.session.delete(subject)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500



@bp.route('/delete_topic/<int:topic_id>', methods=['POST'])
@login_required
def delete_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first()
    if not topic or topic.subject.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Topic not found'}), 404
    try:
        db.session.delete(topic)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/subject/<int:subject_id>/extra_time', methods=['POST'])
@login_required
def set_extra_time(subject_id):
    # Extra time feature disabled
    return jsonify({'success': False, 'error': 'extra_time_disabled'}), 410

@bp.route('/subject/<int:subject_id>/clear_extra_time', methods=['POST'])
@login_required
def clear_extra_time(subject_id):
    # Extra time feature disabled
    return jsonify({'success': False, 'error': 'extra_time_disabled'}), 410

@bp.route('/subject/<int:subject_id>/complete', methods=['POST'])
@login_required
def complete_subject(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
    if not subject:
        return jsonify({'success': False, 'error': 'Subject not found'}), 404
    now = datetime.utcnow()
    # Persist finish timestamp on Subject
    subject.finished_at = now
    
    # Calculate scheduled end time for recommendation
    scheduled_end_time = None
    if subject.end_hour is not None and subject.end_minute is not None:
        today = datetime.utcnow().date()
        scheduled_end_time = datetime.combine(today, datetime.min.time().replace(
            hour=subject.end_hour, 
            minute=subject.end_minute
        ))
    
    # If there's an open session for this subject today without end_time, close it; else log completion stamp
    open_session = StudySession.query.filter(
        StudySession.user_id == current_user.id,
        StudySession.subject_id == subject.id,
        StudySession.end_time.is_(None)
    ).order_by(StudySession.start_time.desc()).first()
    try:
        recommendation = None
        if open_session:
            open_session.end_time = now
            if open_session.start_time:
                elapsed = int((now - open_session.start_time).total_seconds() // 60)
                open_session.actual_duration_minutes = max(elapsed, 0)
            open_session.notes = (open_session.notes or '') + ' finished'
            
            # Generate recommendation based on completion time
            if scheduled_end_time:
                recommendation = open_session.generate_recommendation(scheduled_end_time)
            
            db.session.commit()
            return jsonify({
                'success': True, 
                'completed_at': now.isoformat() + 'Z', 
                'closed_session': open_session.id,
                'recommendation': recommendation,
                'completion_status': open_session.completion_status,
                'pass_status': open_session.pass_status,
                'pass_percentage': open_session.pass_percentage
            })
        else:
            # Create a completion stamp session
            session = StudySession(
                user_id=current_user.id,
                subject_id=subject.id,
                start_time=now,
                end_time=now,
                actual_duration_minutes=0,
                notes='subject_finished'
            )
            
            # Generate recommendation based on completion time
            if scheduled_end_time:
                recommendation = session.generate_recommendation(scheduled_end_time)
                
            db.session.add(session)
            db.session.commit()
            return jsonify({
                'success': True, 
                'completed_at': now.isoformat() + 'Z', 
                'session_id': session.id,
                'recommendation': recommendation,
                'completion_status': session.completion_status
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
