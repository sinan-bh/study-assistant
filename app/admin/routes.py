from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User
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
    
    return render_template('admin/dashboard.html', 
                           total_users=total_users,
                           active_users=active_users,
                           inactive_users=inactive_users)

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
    return render_template('admin/user_detail.html', user=user)

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