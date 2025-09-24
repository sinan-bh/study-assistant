from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models import Subject, Topic


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


@bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@login_required
def delete_topic(topic_id: int):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()
    if topic.subject.user_id != current_user.id:
        return jsonify({'error': 'not found'}), 404
    db.session.delete(topic)
    db.session.commit()
    return jsonify({'success': True})


