from flask import render_template, redirect, url_for, request, jsonify, send_from_directory, current_app
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.models import User, Subject, StudySession, Topic, ExamMode
import os
from datetime import datetime, timedelta

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/index.html', title='Study Assistant')

@bp.route('/dashboard')
@login_required
def dashboard():
    # Clear expired break lazily
    if current_user.lunch_break_until and current_user.lunch_break_until <= datetime.utcnow():
        current_user.lunch_break_until = None
        db.session.commit()

    subjects = Subject.query.filter_by(user_id=current_user.id, is_active=True).all()
    recent_sessions = StudySession.query.filter_by(user_id=current_user.id)\
        .order_by(StudySession.start_time.desc()).limit(5).all()
    today = datetime.today().date()

    # Stats
    active_subjects_count = len(subjects)
    finished_subject_ids = [s.id for s in subjects if (s.finished_at and s.finished_at.date() == today)]
    completed_subjects_count = len(finished_subject_ids)
    pending_subjects_count = max(active_subjects_count - completed_subjects_count, 0)
    # Today's Total Study Time (as total scheduled subject duration)
    def minutes_between(start_h:int, start_m:int, end_h:int, end_m:int) -> int:
        return max((end_h * 60 + end_m) - (start_h * 60 + start_m), 0)
    total_scheduled_minutes = sum(
        minutes_between(s.start_hour or 0, s.start_minute or 0, s.end_hour or 0, s.end_minute or 0)
        for s in subjects
    )

    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute

    # Subjects finished today (used to suppress end-time ringtone)
    # Use Subject.finished_at rather than sessions now
    # finished_subject_ids already computed above

    return render_template('main/dashboard.html', 
                         title='Dashboard',
                         subjects=subjects,
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
                         break_duration_minutes=current_user.break_duration_minutes or 30)

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
        ExamMode.query.filter_by(user_id=current_user.id, subject_id=subject.id).delete(synchronize_session=False)
        # Topics will be deleted by cascade too; explicit bulk delete is optional, but keep safe:
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
    # If there's an open session for this subject today without end_time, close it; else log completion stamp
    open_session = StudySession.query.filter(
        StudySession.user_id == current_user.id,
        StudySession.subject_id == subject.id,
        StudySession.end_time.is_(None)
    ).order_by(StudySession.start_time.desc()).first()
    try:
        if open_session:
            open_session.end_time = now
            if open_session.start_time:
                elapsed = int((now - open_session.start_time).total_seconds() // 60)
                open_session.actual_duration_minutes = max(elapsed, 0)
            open_session.notes = (open_session.notes or '') + ' finished'
            db.session.commit()
            return jsonify({'success': True, 'completed_at': now.isoformat() + 'Z', 'closed_session': open_session.id})
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
            db.session.add(session)
            db.session.commit()
            return jsonify({'success': True, 'completed_at': now.isoformat() + 'Z', 'session_id': session.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
