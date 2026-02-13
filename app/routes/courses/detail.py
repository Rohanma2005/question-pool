from flask import render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import (
    Course,
    ProgrammeCourseOffering,
    CourseOutcome,
    Topic
)
from app.routes.main import super_admin_required
from .routes import courses_bp  # reuse existing blueprint


@courses_bp.route('/<int:course_id>', methods=['GET', 'POST'])
@super_admin_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)

    # =========================
    # ADD COURSE OUTCOME
    # =========================
    if request.method == 'POST':
        co_code = request.form.get('co_code', '').strip()
        co_description = request.form.get('co_description', '').strip()

        if not co_code or not co_description:
            flash('CO code and description are required', 'error')
            return redirect(request.url)

        existing = CourseOutcome.query.filter_by(
            course_id=course.id,
            code=co_code
        ).first()

        if existing:
            flash('CO code already exists for this course', 'error')
        else:
            co = CourseOutcome(
                code=co_code,
                description=co_description,
                course_id=course.id
            )
            db.session.add(co)
            db.session.commit()
            flash('Course Outcome added successfully', 'success')

        return redirect(request.url)

    # =========================
    # LOAD ASSIGNED FACULTIES
    # =========================
    offerings = ProgrammeCourseOffering.query.filter_by(
        course_id=course.id
    ).all()

    assigned_faculties = list({
        offering.faculty for offering in offerings
    })

    # =========================
    # LOAD COs & Topics
    # =========================
    course_outcomes = CourseOutcome.query.filter_by(
        course_id=course.id
    ).all()

    topics = Topic.query.filter_by(
        course_id=course.id
    ).all()

    return render_template(
        'course_detail.html',
        course=course,
        assigned_faculties=assigned_faculties,
        course_outcomes=course_outcomes,
        topics=topics
    )
