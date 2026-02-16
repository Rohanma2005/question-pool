from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Course, Department, Programme, Faculty, ProgrammeCourseOffering, CourseOutcome, Topic
from app.extensions import db
from app.utils.auth import admin_or_hod_required, verify_csrf_token

courses_bp = Blueprint(
    'courses',
    __name__,
    url_prefix='/superadmin/courses'
)


@courses_bp.route('/', methods=['GET', 'POST'])
@admin_or_hod_required
def manage_courses():
    role = session.get('role')

    # =========================
    # Determine Scope
    # =========================
    if role == 'super_admin':
        departments = Department.query.all()
        courses_query = Course.query

    else:  # HOD
        faculty = Faculty.query.get(session['user_id'])
        department = faculty.department

        departments = [department]  # HOD can only see own dept
        courses_query = Course.query.filter_by(
            home_department_id=department.id
        )

    # =========================
    # Handle Create
    # =========================
    if request.method == 'POST':
        if not verify_csrf_token():
            flash('CSRF token invalid', 'error')
            return redirect(request.url)
        
        code = request.form.get('code', '').strip()
        title = request.form.get('title', '').strip()
        department_id = request.form.get('department_id', type=int)

        if not code or not title or not department_id:
            flash('Course code, title, and department are required', 'error')
            return redirect(request.url)

        # HOD cannot create in other departments
        if role == 'faculty':
            if department_id != department.id:
                flash('Not authorized for this department', 'error')
                return redirect(request.url)

        # Check if course code already exists
        if Course.query.filter_by(code=code).first():
            flash('Course code already exists', 'error')
            return redirect(request.url)

        dept = Department.query.get(department_id)
        if not dept:
            flash('Invalid department', 'error')
            return redirect(request.url)

        course = Course(
            code=code,
            title=title,
            home_department_id=department_id
        )

        db.session.add(course)
        db.session.commit()

        flash('Course created successfully', 'success')
        return redirect(request.url)

    courses = courses_query.order_by(Course.code).all()

    return render_template(
        'courses.html',
        courses=courses,
        departments=departments,
        is_superadmin=(role == 'super_admin')
    )

