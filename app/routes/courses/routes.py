from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Course, Department
from app.extensions import db
from app.utils.auth import super_admin_required

courses_bp = Blueprint(
    'courses',
    __name__,
    url_prefix='/superadmin/courses'
)


@courses_bp.route('/', methods=['GET', 'POST'])
@super_admin_required
def manage_courses():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        title = request.form.get('title', '').strip()
        department_id = request.form.get('department_id', type=int)

        if not code or not title or not department_id:
            flash('All fields are required', 'error')
            return redirect(url_for('courses.manage_courses'))

        if Course.query.filter_by(code=code).first():
            flash('Course code already exists', 'error')
            return redirect(url_for('courses.manage_courses'))

        course = Course(
            code=code,
            title=title,
            home_department_id=department_id
        )
        db.session.add(course)
        db.session.commit()

        flash('Course created successfully', 'success')
        return redirect(url_for('courses.manage_courses'))

    courses = Course.query.order_by(Course.code).all()
    departments = Department.query.order_by(Department.name).all()

    return render_template(
        'courses.html',
        courses=courses,
        departments=departments
    )
