from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models import Subject, Topic, ExamSubject, ExamModule, ExamTopic, ExamStudySession
from datetime import datetime


def subject_to_dict(s: Subject):
    return {
        'id': s.id,
        'name': s.name,
        'start_hour': s.start_hour,
        'start_minute': s.start_minute,
        'end_hour': s.end_hour,
        'end_minute': s.end_minute,
        'color': s.color,
        'is_active': s.is_active,
        'topics': [{'id': t.id, 'name': t.name} for t in s.topics.filter_by(is_active=True).all()],
    }


@bp.route('/subjects', methods=['GET'])
@login_required
def get_subjects():
    subjects = Subject.query.filter_by(user_id=current_user.id, is_active=True).all()
    return jsonify([subject_to_dict(s) for s in subjects])


@bp.route('/subjects', methods=['POST'])
@login_required
def create_subject():
    data = request.get_json() or {}
    name = data.get('name')
    start_hour = int(data.get('start_hour', 8))
    start_minute = int(data.get('start_minute', 0))
    end_hour = int(data.get('end_hour', 9))
    end_minute = int(data.get('end_minute', 0))
    if not name:
        return jsonify({'error': 'name required'}), 400
    s = Subject(
        name=name,
        start_hour=start_hour,
        start_minute=start_minute,
        end_hour=end_hour,
        end_minute=end_minute,
        color=data.get('color') or '#007bff',
        user_id=current_user.id,
        is_active=True,
    )
    # Update datetime fields based on hour and minute values
    s.update_datetime_fields()
    
    db.session.add(s)
    db.session.commit()
    return jsonify(subject_to_dict(s)), 201


@bp.route('/subjects/<int:subject_id>/topics', methods=['POST'])
@login_required
def create_topic(subject_id: int):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    t = Topic(name=name, subject_id=subject.id, is_active=True)
    db.session.add(t)
    db.session.commit()
    return jsonify({'id': t.id, 'name': t.name}), 201


@bp.route('/subjects/<int:subject_id>', methods=['DELETE'])
@login_required
def delete_subject(subject_id: int):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    return jsonify({'success': True})


# Exam Mode API Endpoints

def exam_subject_to_dict(es: ExamSubject):
    return {
        'id': es.id,
        'name': es.name,
        'start_date': es.start_date.isoformat() if es.start_date else None,
        'end_date': es.end_date.isoformat() if es.end_date else None,
        'total_modules': es.total_modules,
        'is_active': es.is_active,
        'modules': [exam_module_to_dict(m) for m in es.modules.all()]
    }

def exam_module_to_dict(em: ExamModule):
    return {
        'id': em.id,
        'module_number': em.module_number,
        'topics': [exam_topic_to_dict(t) for t in em.topics.all()]
    }

def exam_topic_to_dict(et: ExamTopic):
    return {
        'id': et.id,
        'name': et.name,
        'description': et.description,
        'is_completed': et.is_completed
    }

@bp.route('/exam-subjects', methods=['GET'])
@login_required
def get_exam_subjects():
    exam_subjects = ExamSubject.query.filter_by(user_id=current_user.id, is_active=True).all()
    return jsonify([exam_subject_to_dict(es) for es in exam_subjects])

@bp.route('/exam-subjects', methods=['POST'])
@login_required
def create_exam_subject():
    data = request.get_json() or {}
    name = data.get('name')
    start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d') if data.get('start_date') else None
    end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d') if data.get('end_date') else None
    total_modules = int(data.get('total_modules', 1))
    
    if not name:
        return jsonify({'error': 'name required'}), 400
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date required'}), 400
    if total_modules < 1:
        return jsonify({'error': 'total_modules must be at least 1'}), 400
    
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
    return jsonify(exam_subject_to_dict(es)), 201

@bp.route('/exam-modules/<int:module_id>/topics', methods=['POST'])
@login_required
def create_exam_topic(module_id: int):
    module = ExamModule.query.filter_by(id=module_id).first_or_404()
    # Check if user owns this module
    if module.exam_subject.user_id != current_user.id:
        return jsonify({'error': 'not found'}), 404
    
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': 'name required'}), 400
    
    et = ExamTopic(
        name=name,
        description=description,
        exam_module_id=module_id,
        is_completed=False
    )
    db.session.add(et)
    db.session.commit()
    return jsonify(exam_topic_to_dict(et)), 201

@bp.route('/exam-topics/<int:topic_id>/toggle-complete', methods=['POST'])
@login_required
def toggle_exam_topic_complete(topic_id: int):
    topic = ExamTopic.query.filter_by(id=topic_id).first_or_404()
    # Check if user owns this topic
    if topic.exam_module.exam_subject.user_id != current_user.id:
        return jsonify({'error': 'not found'}), 404
    
    topic.is_completed = not topic.is_completed
    db.session.commit()
    return jsonify(exam_topic_to_dict(topic))

@bp.route('/exam-modules/<int:module_id>/start-session', methods=['POST'])
@login_required
def start_exam_session(module_id: int):
    module = ExamModule.query.filter_by(id=module_id).first_or_404()
    # Check if user owns this module
    if module.exam_subject.user_id != current_user.id:
        return jsonify({'error': 'not found'}), 404
    
    data = request.get_json() or {}
    end_time = datetime.strptime(data.get('end_time'), '%Y-%m-%dT%H:%M:%S') if data.get('end_time') else None
    
    if not end_time:
        return jsonify({'error': 'end_time required'}), 400
    
    session = ExamStudySession(
        user_id=current_user.id,
        exam_module_id=module_id,
        start_time=datetime.utcnow(),
        end_time=end_time
    )
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'id': session.id,
        'start_time': session.start_time.isoformat(),
        'end_time': session.end_time.isoformat() if session.end_time else None
    }), 201

@bp.route('/exam-subjects/<int:subject_id>', methods=['DELETE'])
@login_required
def delete_exam_subject(subject_id: int):
    subject = ExamSubject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/exam-topics/<int:topic_id>', methods=['DELETE'])
@login_required
def delete_exam_topic(topic_id: int):
    topic = ExamTopic.query.filter_by(id=topic_id).first_or_404()
    # Check if user owns this topic
    if topic.exam_module.exam_subject.user_id != current_user.id:
        return jsonify({'error': 'not found'}), 404
    
    db.session.delete(topic)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@login_required
def delete_topic(topic_id: int):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()
    if topic.subject.user_id != current_user.id:
        return jsonify({'error': 'not found'}), 404
    db.session.delete(topic)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/exam-modules/<int:module_id>/topics', methods=['GET'])
@login_required
def get_exam_topics(module_id: int):
    module = ExamModule.query.filter_by(id=module_id).first_or_404()
    # Check if user owns this module
    if module.exam_subject.user_id != current_user.id:
        return jsonify({'error': 'not found'}), 404
    
    topics = ExamTopic.query.filter_by(exam_module_id=module_id).all()
    return jsonify([exam_topic_to_dict(t) for t in topics])