from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from app.extensions import db
from app.models import Template, Course, Faculty
from app.utils.auth import admin_or_hod_required

templates_bp = Blueprint(
    'templates',
    __name__,
    url_prefix='/superadmin/templates'
)

@templates_bp.route('', methods=['GET', 'POST'])
@admin_or_hod_required
def manage_template():

    role = session.get('role')
    user_id = session.get('user_id')

    # =========================================
    # Determine Course Scope
    # =========================================
    if role == 'super_admin':
        courses = Course.query.order_by(Course.code).all()

    elif role == 'faculty':
        faculty = Faculty.query.get(user_id)

        # If HOD → courses in department
        if faculty.department.hod_id == faculty.id:
            courses = Course.query.filter_by(
                home_department_id=faculty.department.id
            ).all()
        else:
            # Normal faculty → assigned courses only
            offerings = ProgrammeCourseOffering.query.filter_by(
                faculty_id=faculty.id
            ).all()

            course_ids = {o.course_id for o in offerings}
            courses = Course.query.filter(
                Course.id.in_(course_ids)
            ).all()

    else:
        flash("Unauthorized", "error")
        return redirect(url_for('main.login'))

    # =========================================
    # Handle Template Creation
    # =========================================
    if request.method == 'POST':

        course_id = request.form.get('course_id', type=int)
        total_marks = request.form.get('total_marks', type=int)
        duration = request.form.get('duration_minutes', type=int)
        section_count = request.form.get('section_count', type=int)

        course = Course.query.get_or_404(course_id)

        # Additional security check
        if role == 'faculty':
            faculty = Faculty.query.get(user_id)

            if faculty.department.hod_id != faculty.id:
                # Normal faculty must be assigned
                assigned_ids = {
                    o.course_id
                    for o in ProgrammeCourseOffering.query.filter_by(
                        faculty_id=faculty.id
                    )
                }
                if course_id not in assigned_ids:
                    flash("Not authorized for this course", "error")
                    return redirect(request.url)
            else:
                # HOD → must be dept owned
                if course.home_department_id != faculty.department.id:
                    flash("Not authorized for this course", "error")
                    return redirect(request.url)

        # Ensure only one template
        if Template.query.filter_by(course_id=course_id).first():
            flash("Template already exists for this course", "error")
            return redirect(request.url)

        # Collect sections
        sections = []
        for i in range(section_count):
            sections.append({
                "section": request.form.get(f'section_{i}_name'),
                "question_type": request.form.get(f'section_{i}_type'),
                "mark_per_question": request.form.get(
                    f'section_{i}_mark', type=int
                ),
                "number_of_questions": request.form.get(
                    f'section_{i}_count', type=int
                )
            })

        # Validate total marks
        calculated_total = sum(
            s["mark_per_question"] * s["number_of_questions"]
            for s in sections
        )

        if calculated_total != total_marks:
            flash("Section marks do not match total marks", "error")
            return redirect(request.url)

        template = Template(
            course_id=course_id,
            duration_minutes=duration,
            total_marks=total_marks,
            categories=sections
        )

        db.session.add(template)
        db.session.commit()

        flash("Template created successfully", "success")
        return redirect(request.url)

    return render_template(
        "template_management.html",
        courses=courses
    )
