from flask import session, redirect, url_for, flash, request
from functools import wraps
import secrets
from ..models import Faculty

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to login first', 'error')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def faculty_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'faculty':
            flash('You need to login first', 'error')
            return redirect(url_for('faculty_auth.faculty_login'))
        return f(*args, **kwargs)
    return decorated_function

def verify_csrf_token():
    """Verify CSRF token from form or headers"""
    token = session.get('csrf_token')
    if not token:
        return False
    
    form_token = request.form.get('csrf_token', '') or request.headers.get('X-CSRF-Token', '')
    return secrets.compare_digest(token, form_token)

def hod_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'faculty':
            return redirect(url_for('main.login'))

        faculty = Faculty.query.get(session.get('user_id'))
        if not faculty or faculty.department.hod_id != faculty.id:
            return redirect(url_for('faculty.faculty_dashboard'))

        return f(*args, **kwargs)

    return decorated_function

def get_current_user():
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'super_admin':
        return role, None

    if role == 'faculty':
        faculty = Faculty.query.get(user_id)
        return role, faculty

    return None, None

def admin_or_hod_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role')

        # Super Admin allowed
        if role == 'super_admin':
            return f(*args, **kwargs)

        # Faculty → check if HOD
        if role == 'faculty':
            faculty = Faculty.query.get(session.get('user_id'))
            if faculty and faculty.department.hod_id == faculty.id:
                return f(*args, **kwargs)

        return redirect(url_for('main.login'))

    return decorated_function