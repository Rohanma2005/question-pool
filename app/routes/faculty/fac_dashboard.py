from flask import Blueprint, render_template, session, redirect, url_for
from app.models import ProgrammeCourseOffering, Course, Programme
from app.routes.main import login_required

faculty_dashboard_bp = Blueprint(
    'faculty_dashboard',
    __name__,
    url_prefix='/faculty'
)


@faculty_dashboard_bp.route('/dashboard')
@login_required
def dashboard():

    if session.get('role') != 'faculty':
        return redirect(url_for('main.superadmin_dashboard'))

    faculty_id = session.get('faculty_id')

    offerings = ProgrammeCourseOffering.query.filter_by(
        faculty_id=faculty_id
    ).all()

    return render_template(
        'faculty_dashboard.html',
        offerings=offerings
    )
