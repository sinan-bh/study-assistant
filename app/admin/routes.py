from flask import render_template, redirect, url_for, flash, request, jsonify

from flask_login import login_required, current_user

from app import db

from app.models import User, AdminChat, ExamSubject, ExamModule, ExamTopic

from app.admin import bp

from functools import wraps

from datetime import datetime, timedelta

from sqlalchemy import func

import json



def admin_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated or not current_user.is_admin:

            flash('You need to be an admin to access this page.', 'danger')

            return redirect(url_for('main.index'))

        return f(*args, **kwargs)

    return decorated_function

    

@bp.route('/module-completion')

@login_required

@admin_required

def module_completion():

    users = User.query.all()

    return render_template('admin/module_completion.html', users=users)



@bp.route('/api/admin/subjects')

@login_required

@admin_required

def get_subjects():

    user_id = request.args.get('user_id', '')

    

    # Get both regular subjects and exam subjects

    from app.models import Subject

    

    subjects = []

    

    # Get regular subjects

    regular_subjects_query = Subject.query

    if user_id:

        regular_subjects_query = regular_subjects_query.filter(Subject.user_id == user_id)

    

    regular_subjects = regular_subjects_query.all()

    for subject in regular_subjects:

        subjects.append({

            'id': f"regular_{subject.id}",

            'name': f"{subject.name} (Regular)",

            'type': 'regular'

        })

    

    # Get exam subjects

    exam_subjects_query = ExamSubject.query

    if user_id:

        # Filter subjects that have modules with study sessions by this user

        exam_subjects_query = exam_subjects_query.join(ExamModule).join(ExamModule.study_sessions).filter(

            ExamModule.study_sessions.any(user_id=user_id)

        ).distinct()

    

    exam_subjects = exam_subjects_query.all()

    for subject in exam_subjects:

        subjects.append({

            'id': f"exam_{subject.id}",

            'name': f"{subject.name} (Exam)",

            'type': 'exam'

        })

    

    return jsonify(subjects)



@bp.route('/api/admin/module-completion')

@login_required

@admin_required

def get_module_completion():

    user_id = request.args.get('user_id', '')

    subject_id = request.args.get('subject_id', '')

    status = request.args.get('status', '')

    

    result = []

    

    # Handle regular subjects

    if not subject_id or subject_id.startswith('regular_'):

        from app.models import Subject, Topic, StudySession

        

        # Base query for regular subjects

        subjects_query = Subject.query

        

        # Apply filters

        if subject_id and subject_id.startswith('regular_'):

            actual_subject_id = subject_id.replace('regular_', '')

            subjects_query = subjects_query.filter(Subject.id == actual_subject_id)

        

        if user_id:

            subjects_query = subjects_query.filter(Subject.user_id == user_id)

        

        subjects = subjects_query.all()

        

        for subject in subjects:

            # Get topics for this subject

            topics_query = Topic.query.filter(Topic.subject_id == subject.id, Topic.is_active == True)

            topics = topics_query.all()

            total_topics = len(topics)

            

            # Count completed topics (topics that have study sessions)

            completed_topics = 0

            if user_id:

                # Count topics that have study sessions by this user

                for topic in topics:

                    has_sessions = StudySession.query.filter(

                        StudySession.user_id == user_id,

                        StudySession.topic_id == topic.id

                    ).first() is not None

                    if has_sessions:

                        completed_topics += 1

            else:

                # Count topics that have any study sessions

                for topic in topics:

                    has_sessions = StudySession.query.filter(

                        StudySession.topic_id == topic.id

                    ).first() is not None

                    if has_sessions:

                        completed_topics += 1

            

            # For regular subjects, we treat each subject as a single "module"

            is_completed = (completed_topics == total_topics and total_topics > 0)

            

            # Apply completion status filter if specified

            if status == 'completed' and not is_completed:

                continue

            elif status == 'incomplete' and is_completed:

                continue

            

            # Create a single module representation for regular subjects

            processed_modules = [{

                'id': subject.id,

                'module_number': 1,

                'completed_topics': completed_topics,

                'total_topics': total_topics,

                'is_completed': is_completed

            }]

            

            result.append({

                'id': f"regular_{subject.id}",

                'name': f"{subject.name} (Regular)",

                'completed_modules': 1 if is_completed else 0,

                'total_modules': 1,

                'modules': processed_modules,

                'type': 'regular'

            })

    

    # Handle exam subjects

    if not subject_id or subject_id.startswith('exam_'):

        # Base query for exam subjects

        subjects_query = ExamSubject.query

        

        # Apply filters

        if subject_id and subject_id.startswith('exam_'):

            actual_subject_id = subject_id.replace('exam_', '')

            subjects_query = subjects_query.filter(ExamSubject.id == actual_subject_id)

        

        subjects = subjects_query.all()

        

        for subject in subjects:

            modules_query = ExamModule.query.filter(ExamModule.exam_subject_id == subject.id)

            

            # Get all modules for this subject

            modules = modules_query.all()

            

            # Process modules to include completion data

            processed_modules = []

            completed_modules_count = 0

            

            for module in modules:

                # Get topics for this module

                topics = ExamTopic.query.filter(ExamTopic.exam_module_id == module.id).all()

                total_topics = len(topics)

                

                # If filtering by user, check which topics they've completed

                completed_topics = 0

                if user_id:

                    # Get study sessions for this user and module

                    user_sessions = ExamStudySession.query.filter(

                        ExamStudySession.user_id == user_id,

                        ExamStudySession.exam_module_id == module.id

                    ).all()

                    

                    # If user has study sessions for this module, count completed topics

                    if user_sessions:

                        completed_topics = ExamTopic.query.filter(

                            ExamTopic.exam_module_id == module.id,

                            ExamTopic.is_completed == True

                        ).count()

                else:

                    completed_topics = ExamTopic.query.filter(

                        ExamTopic.exam_module_id == module.id,

                        ExamTopic.is_completed == True

                    ).count()

                

                # Check if module is fully completed

                is_completed = (completed_topics == total_topics and total_topics > 0)

                

                # Apply completion status filter if specified

                if status == 'completed' and not is_completed:

                    continue

                elif status == 'incomplete' and is_completed:

                    continue

                    

                if is_completed:

                    completed_modules_count += 1

                    

                processed_modules.append({

                    'id': module.id,

                    'module_number': module.module_number,

                    'completed_topics': completed_topics,

                    'total_topics': total_topics,

                    'is_completed': is_completed

                })

            

            # Skip subjects with no modules after filtering

            if not processed_modules:

                continue

                

            result.append({

                'id': f"exam_{subject.id}",

                'name': f"{subject.name} (Exam)",

                'completed_modules': completed_modules_count,

                'total_modules': len(modules),

                'modules': processed_modules,

                'type': 'exam'

            })

    

    return jsonify(result)



@bp.route('/api/admin/module-topics/<module_id>')

@login_required

@admin_required

def get_module_topics(module_id):

    user_id = request.args.get('user_id', '')

    

    result = []

    

    # Handle regular subjects (module_id is actually subject_id for regular subjects)

    if str(module_id).startswith('regular_') or not str(module_id).isdigit():

        from app.models import Subject, Topic, StudySession

        

        # Extract subject ID from module_id

        if str(module_id).startswith('regular_'):

            subject_id = module_id.replace('regular_', '')

        else:

            subject_id = module_id

            

        # Get topics for this regular subject

        topics = Topic.query.filter(Topic.subject_id == subject_id, Topic.is_active == True).all()

        

        for topic in topics:

            # Check if topic is completed (has study sessions)

            is_completed = False

            if user_id:

                # Check if this user has study sessions for this topic

                user_sessions = StudySession.query.filter(

                    StudySession.user_id == user_id,

                    StudySession.topic_id == topic.id

                ).first()

                is_completed = user_sessions is not None

                

                # Get user details if user has sessions

                if user_sessions:

                    user = User.query.get(user_id)

                    if user:

                        topic_data = {

                            'id': topic.id,

                            'name': topic.name,

                            'description': topic.description,

                            'is_completed': is_completed,

                            'user': {

                                'id': user.id,

                                'username': user.username,

                                'email': user.email

                            }

                        }

                    else:

                        topic_data = {

                            'id': topic.id,

                            'name': topic.name,

                            'description': topic.description,

                            'is_completed': is_completed

                        }

                else:

                    topic_data = {

                        'id': topic.id,

                        'name': topic.name,

                        'description': topic.description,

                        'is_completed': is_completed

                    }

            else:

                # Check if any user has study sessions for this topic

                any_sessions = StudySession.query.filter(

                    StudySession.topic_id == topic.id

                ).first()

                is_completed = any_sessions is not None

                

                topic_data = {

                    'id': topic.id,

                    'name': topic.name,

                    'description': topic.description,

                    'is_completed': is_completed

                }

            

            result.append(topic_data)

    

    # Handle exam subjects

    else:

        topics = ExamTopic.query.filter(ExamTopic.exam_module_id == module_id).all()

        

        for topic in topics:

            topic_data = {

                'id': topic.id,

                'name': topic.name,

                'description': topic.description,

                'is_completed': topic.is_completed

            }

            

            # Add user information if user_id is provided

            if user_id:

                # Check if this user has study sessions for this topic's module

                user_sessions = ExamStudySession.query.filter(

                    ExamStudySession.user_id == user_id,

                    ExamStudySession.exam_module_id == module_id

                ).first()

                

                if user_sessions:

                    # Get user details

                    user = User.query.get(user_id)

                    if user:

                        topic_data['user'] = {

                            'id': user.id,

                            'username': user.username,

                            'email': user.email

                        }

            

            result.append(topic_data)

    

    return jsonify(result)



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

    user_tasks = (
        db.session.query(
            User.username.label("username"),
            func.count(StudySession.id).label('count')
        )
        .join(User, User.id == StudySession.user_id)
        .group_by(User.username)
        .all()
    )

    

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


