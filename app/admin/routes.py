from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, AdminChat
from app.admin import bp
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Only count users that are not the current user (admin)
    total_users = User.query.filter(User.id != current_user.id).count()
    active_users = User.query.filter(User.id != current_user.id, User.is_active==True).count()
    inactive_users = User.query.filter(User.id != current_user.id, User.is_active==False).count()
    
    # Get today's created tasks data for pie chart
    from app.models import StudySession
    from sqlalchemy import func
    import datetime
    
    # Get today's date
    today = datetime.datetime.now().date()
    
    # Count all tasks by user (not just today's)
    user_tasks = db.session.query(
        User.username.label("username"),
        func.count(StudySession.id).label('count')
    ).join(User, User.id == StudySession.user_id)\
    .group_by(User.username).all()
    
    # Prepare data for the pie chart
    if user_tasks:
        task_labels = [task[0] for task in user_tasks]
        task_counts = [task[1] for task in user_tasks]
    else:
        task_labels = ["No Tasks"]
        task_counts = [0]
    
    return render_template('admin/dashboard.html', 
                           total_users=total_users,
                           active_users=active_users,
                           inactive_users=inactive_users,
                           status_labels=task_labels,
                           status_counts=task_counts)

@bp.route('/users')
@login_required
@admin_required
def users():
    users_list = User.query.filter(User.id != current_user.id).all()
    return render_template('admin/users.html', users=users_list)

@bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    # Get chat messages for this user
    chats = AdminChat.query.filter_by(user_id=user_id).order_by(AdminChat.timestamp).all()
    return render_template('admin/user_detail.html', user=user, chats=chats)

@bp.route('/subjects')
@login_required
@admin_required
def subjects():
    from app.models import Subject
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@bp.route('/quizzes')
@login_required
@admin_required
def quizzes():
    from app.models import Quiz, Subject, User
    try:
        quizzes = Quiz.query.all()
        
        # Get all subjects from all users
        all_subjects = []
        
        # Get all regular users (non-admin)
        users = User.query.filter(User.is_admin == False).all()
        
        # Get subjects for each user
        for user in users:
            user_subjects = Subject.query.filter_by(user_id=user.id).all()
            all_subjects.extend(user_subjects)
        
        # If no subjects exist, create a default one
        if not all_subjects:
            default_subject = Subject(
                name="General",
                description="Default subject for quizzes",
                user_id=current_user.id
            )
            db.session.add(default_subject)
            db.session.commit()
            all_subjects = [default_subject]
            
        return render_template('admin/quizzes.html', quizzes=quizzes, subjects=all_subjects)
    except Exception as e:
        print(f"Error loading quizzes: {e}")
        # If Quiz model doesn't exist
        return render_template('admin/quizzes.html', quizzes=[], subjects=[])

@bp.route('/quizzes/<int:quiz_id>')
@login_required
@admin_required
def view_quiz(quiz_id):
    from app.models import Quiz
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        return render_template('admin/quiz_detail.html', quiz=quiz)
    except Exception as e:
        flash(f'Error loading quiz: {str(e)}', 'danger')
        return redirect(url_for('admin.quizzes'))

@bp.route('/quiz/questions/add', methods=['POST'])
@login_required
@admin_required
def add_quiz_question():
    try:
        data = request.get_json()
        from app.models import QuizQuestion, QuizOption
        
        # Create new question
        question = QuizQuestion(
            question_text=data['question_text'],
            quiz_id=data['quiz_id']
        )
        db.session.add(question)
        db.session.flush()  # Get question ID before committing
        
        # Create options
        for option_data in data['options']:
            option = QuizOption(
                option_text=option_data['option_text'],
                is_correct=option_data['is_correct'],
                question_id=question.id
            )
            db.session.add(option)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/questions/<int:question_id>/options', methods=['GET'])
@login_required
@admin_required
def get_question_options(question_id):
    try:
        from app.models import QuizOption
        options = QuizOption.query.filter_by(question_id=question_id).all()
        options_data = [{'id': option.id, 'text': option.text, 'is_correct': option.is_correct} for option in options]
        return jsonify({'success': True, 'options': options_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/questions/<int:question_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_question(question_id):
    try:
        data = request.get_json()
        from app.models import QuizQuestion, QuizOption
        question = QuizQuestion.query.get_or_404(question_id)
        question.question_text = data['question_text']
        
        # Update options
        for option_data in data['options']:
            option = QuizOption.query.get(option_data['id'])
            if option:
                option.option_text = option_data['option_text']
                option.is_correct = option_data['is_correct']
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    try:
        from app.models import QuizQuestion, QuizOption
        question = QuizQuestion.query.get_or_404(question_id)
        
        # Delete associated options first
        QuizOption.query.filter_by(question_id=question_id).delete()
        
        # Delete question
        db.session.delete(question)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/subjects/<int:subject_id>')
@login_required
@admin_required
def subject_detail(subject_id):
    from app.models import Subject, Topic
    subject = Subject.query.filter_by(id=subject_id).first_or_404()
    topics = Topic.query.filter_by(subject_id=subject.id, is_active=True).all()
    
    # Fetch quizzes for this subject
    quizzes = []
    try:
        from app.models import Quiz
        quizzes = Quiz.query.filter_by(subject_id=subject_id).all()
    except:
        # If Quiz model doesn't exist, we'll pass an empty list
        pass
        
    return render_template('admin/subject_detail.html', subject=subject, topics=topics, quizzes=quizzes)

@bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow admins to block themselves
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot block yourself'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'blocked'
    return jsonify({
        'success': True, 
        'message': f'User {user.username} has been {status}',
        'is_active': user.is_active
    })

# Quiz Routes
@bp.route('/quizzes/create-with-question', methods=['POST'])
@login_required
@admin_required
def create_quiz_with_question():
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Create the quiz
        from app.models import Quiz, QuizQuestion, QuizOption, Subject
        
        # Create or get subject
        subject_name = data.get('subject_name')
        subject_id = None
        
        if subject_name:
            # Check if subject with this name already exists
            subject = Subject.query.filter_by(name=subject_name).first()
            if not subject:
                # Create a new subject with the provided name
                subject = Subject(
                    name=subject_name,
                    description=f"Subject for {data['title']} quiz",
                    user_id=current_user.id
                )
                db.session.add(subject)
                db.session.flush()  # Get the ID without committing
            subject_id = subject.id
        else:
            # Fallback to default subject if no name provided
            subject = Subject.query.filter_by(user_id=current_user.id).first()
            if not subject:
                # Create a default subject if none exists
                subject = Subject(
                    name="General",
                    description="Default subject for quizzes",
                    user_id=current_user.id
                )
                db.session.add(subject)
                db.session.flush()  # Get the ID without committing
            subject_id = subject.id
        
        # First create the quiz
        quiz = Quiz(
            title=data['title'],
            description=data.get('description', ''),
            subject_id=subject_id
        )
        
        db.session.add(quiz)
        db.session.flush()  # Get the quiz ID without committing
        
        # Create the question if provided
        question_data = data.get('question')
        if question_data:
            new_question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=question_data.get('text')
            )
            
            db.session.add(new_question)
            db.session.flush()  # Get the question ID
            
            # Create the options
            options_data = question_data.get('options', [])
            for option_data in options_data:
                new_option = QuizOption(
                    question_id=new_question.id,
                    option_text=option_data.get('text'),
                    is_correct=option_data.get('is_correct', False)
                )
                db.session.add(new_option)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz created successfully',
            'quiz_id': quiz.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/quizzes/create', methods=['POST'])
@login_required
@admin_required
def create_quiz():
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Create new quiz
        from app.models import Quiz, Subject
        
        # Create quiz with default subject
        default_subject = Subject.query.first()
        if not default_subject:
            default_subject = Subject(name="General", description="Default subject", user_id=current_user.id)
            db.session.add(default_subject)
            db.session.flush()
        
        quiz = Quiz(
            title=data['title'],
            description=data.get('description', ''),
            subject_id=default_subject.id
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz created successfully',
            'quiz_id': quiz.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/quizzes/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(quiz_id):
    from app.models import Quiz, QuizQuestion, QuizOption
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'GET':
        # Get the quiz with its questions and options
        questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
        
        # Prepare questions data with their options
        questions_data = []
        for question in questions:
            options = QuizOption.query.filter_by(question_id=question.id).all()
            questions_data.append({
                'id': question.id,
                'text': question.question_text,
                'options': options
            })
        
        return render_template('admin/edit_quiz.html', 
                              quiz=quiz, 
                              questions=questions_data,
                              subject=quiz.subject)
    
    # Handle POST request to update quiz
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        from app.models import Subject
        quiz.title = data['title']
        quiz.description = data.get('description', '')
        
        # Handle subject name
        subject_name = data.get('subject_name')
        if subject_name:
            # Check if subject with this name already exists
            subject = Subject.query.filter_by(name=subject_name).first()
            if not subject:
                # Create a new subject with the provided name
                subject = Subject(
                    name=subject_name,
                    description=f"Subject for {data['title']} quiz",
                    user_id=current_user.id
                )
                db.session.add(subject)
                db.session.flush()  # Get the ID without committing
            quiz.subject_id = subject.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/quizzes/<int:quiz_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_quiz(quiz_id):
    from app.models import Quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    try:
        db.session.delete(quiz)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/quizzes/<int:quiz_id>/questions/add', methods=['POST'])
@login_required
@admin_required
def add_question(quiz_id):
    from app.models import Quiz, QuizQuestion, QuizOption
    quiz = Quiz.query.get_or_404(quiz_id)
    data = request.json
    
    if not data or 'question_text' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Create new question
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=data['question_text'],
            question_type=data.get('question_type', 'multiple_choice'),
            points=data.get('points', 1)
        )
        
        db.session.add(question)
        db.session.commit()
        
        # Add options if provided
        if 'options' in data and isinstance(data['options'], list):
            for option_data in data['options']:
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data.get('text', ''),
                    is_correct=option_data.get('is_correct', False)
                )
                db.session.add(option)
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question added successfully',
            'question_id': question.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
