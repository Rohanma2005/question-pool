from flask import Blueprint, render_template, session, redirect, url_for
from app.models import Faculty, ProgrammeCourseOffering
from app.routes.main import login_required

fac_dashboard_bp = Blueprint(
    'faculty',
    __name__,
    url_prefix='/faculty'
)


@fac_dashboard_bp.route('/dashboard')
@login_required
def faculty_dashboard():
    if session.get('role') != 'faculty':
        return redirect(url_for('main.login'))

    faculty = Faculty.query.get_or_404(session['user_id'])

    offerings = ProgrammeCourseOffering.query.filter_by(
        faculty_id=faculty.id
    ).all()

    return render_template(
        'faculty_dashboard.html',
        faculty=faculty,
        offerings=offerings
    )


@fac_dashboard_bp.route('/hod-dashboard')
@login_required
def hod_dashboard():
    if session.get('role') != 'faculty':
        return redirect(url_for('main.login'))

    faculty = Faculty.query.get_or_404(session['user_id'])

    if faculty.department.hod_id != faculty.id:
        return redirect(url_for('faculty.faculty_dashboard'))

    return render_template(
        'hod_dashboard.html',
        faculty=faculty
    )
