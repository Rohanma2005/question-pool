from flask import session, redirect, url_for, flash, request
from functools import wraps
import secrets

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to login first', 'error')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'super_admin':
            flash('Access denied', 'error')
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