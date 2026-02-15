from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Faculty
from werkzeug.security import check_password_hash

faculty_auth_bp = Blueprint(
    'faculty_auth',
    __name__,
    url_prefix='/faculty'
)


@faculty_auth_bp.route('/login', methods=['GET', 'POST'])
def faculty_login():

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        faculty = Faculty.query.filter_by(email=email).first()

        if faculty and check_password_hash(faculty.password_hash, password):

            session.clear()
            session['user_id'] = faculty.id
            session['role'] = 'faculty'
            session['faculty_id'] = faculty.id

            flash('Login successful', 'success')
            return redirect(url_for('faculty_dashboard.dashboard'))

        flash('Invalid credentials', 'error')

    return render_template('faculty_login.html')
