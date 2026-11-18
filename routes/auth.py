from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models import UserModel
from database import log_activity
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        student_id = request.form.get('student_id', '').strip().upper()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        errors = []
        if not name or len(name) < 2:
            errors.append('Please provide your full legal name.')
        if not email or '@' not in email or '.' not in email:
            errors.append('Please provide a valid email address.')
        if not student_id or len(student_id) < 3:
            errors.append('Please provide a valid Student ID number.')
        if not department:
            errors.append('Please select your academic department.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if UserModel.get_by_email(email):
            errors.append(f'An account with email "{email}" already exists.')

        if UserModel.get_by_student_id(student_id):
            errors.append(f'An account with Student ID "{student_id}" is already registered.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html', 
                                   departments=Config.DEPARTMENTS,
                                   form_data=request.form)

        # Create user
        try:
            user_id = UserModel.create(name, email, student_id, department, phone, password, role='student')
            log_activity(user_id, 'USER_REGISTERED', f"New student registered: {student_id} ({name})")
            flash('Registration successful! Please log in to access your dashboard.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred during registration. Please try again: {str(e)}', 'danger')

    return render_template('register.html', departments=Config.DEPARTMENTS, form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        login_identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        if not login_identifier or not password:
            flash('Please enter both your Email / Student ID and your password.', 'danger')
            return render_template('login.html', identifier=login_identifier)

        # Allow login by email or by student ID
        user = UserModel.get_by_email(login_identifier)
        if not user:
            user = UserModel.get_by_student_id(login_identifier)

        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email/student ID or password. Please try again.', 'danger')
            return render_template('login.html', identifier=login_identifier)

        # Set session
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['student_id'] = user['student_id']
        session['user_role'] = user['role']
        session['department'] = user['department']

        if remember:
            session.permanent = True

        log_activity(user['id'], 'USER_LOGIN', f"User {user['name']} logged in.")
        flash(f"Welcome back, {user['name']}!", 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    user_name = session.get('user_name', 'User')
    if user_id:
        log_activity(user_id, 'USER_LOGOUT', f"User {user_name} logged out.")
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
