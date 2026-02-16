from pydoc_data.topics import topics
from flask import render_template, request, redirect, session, url_for, flash
from app.extensions import db
from app.models import (
    Course,
    ProgrammeCourseOffering,
    CourseOutcome,
    Topic
)
from app.utils.auth import super_admin_required, login_required
from .routes import courses_bp  # reuse existing blueprint


@courses_bp.route('/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    is_superadmin = session.get('role') == 'super_admin'


    # =========================
    # HANDLE POST REQUESTS
    # =========================
    if request.method == 'POST':

        form_type = request.form.get('form_type')

        # -------------------------
        # ADD COURSE OUTCOME
        # -------------------------
        if form_type == 'add_co':
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

        # -------------------------
        # ADD TOPIC
        # -------------------------
        elif form_type == 'add_topic':
            topic_code = request.form.get('topic_code', '').strip()
            topic_title = request.form.get('topic_title', '').strip()
            co_id = request.form.get('co_id', type=int)

            if not topic_code or not topic_title or not co_id:
                flash('Topic code, description, and CO are required', 'error')
                return redirect(request.url)

            # Validate CO belongs to this course
            co = CourseOutcome.query.filter_by(
                id=co_id,
                course_id=course.id
            ).first()

            if not co:
                flash('Invalid Course Outcome selected', 'error')
                return redirect(request.url)

            # Prevent duplicate topic code within same course
            existing = Topic.query.filter_by(
                course_id=course.id,
                code=topic_code
            ).first()

            if existing:
                flash('Topic code already exists for this course', 'error')
                return redirect(request.url)

            topic = Topic(
                code=topic_code,
                title=topic_title,
                course_id=course.id,
                co_id=co.id
            )

            db.session.add(topic)
            db.session.commit()

            flash('Topic added successfully', 'success')
            return redirect(request.url)

    # =========================
    # LOAD DATA FOR VIEW
    # =========================

    offerings = ProgrammeCourseOffering.query.filter_by(
        course_id=course.id
    ).all()

    assigned_faculties = list({
        offering.faculty for offering in offerings
    })

    course_outcomes = CourseOutcome.query.filter_by(
        course_id=course.id
    ).all()

    topics = Topic.query.filter_by(
        course_id=course.id
    ).all()

    role = session.get('role')

    if role == 'super_admin':
         layout_template = 'layout_dashboard.html'
    else:
        layout_template = 'layout_faculty.html' 

    return render_template(
        'course_detail.html',
        course=course,
        assigned_faculties=assigned_faculties,
        course_outcomes=course_outcomes,
        topics=topics,
        is_superadmin=is_superadmin,
        layout_template=layout_template
    )




@courses_bp.route(
    '/co/<int:co_id>/edit',
    methods=['POST']
)
@super_admin_required
def edit_course_outcome(co_id):
    co = CourseOutcome.query.get_or_404(co_id)

    new_code = request.form.get('co_code', '').strip()
    new_description = request.form.get('co_description', '').strip()

    if not new_code or not new_description:
        flash('CO code and description are required', 'error')
        return redirect(request.referrer)

    # Prevent duplicate CO code in same course
    existing = CourseOutcome.query.filter(
        CourseOutcome.course_id == co.course_id,
        CourseOutcome.code == new_code,
        CourseOutcome.id != co.id
    ).first()

    if existing:
        flash('Another CO with this code already exists', 'error')
        return redirect(request.referrer)

    co.code = new_code
    co.description = new_description

    db.session.commit()

    flash('Course Outcome updated successfully', 'success')
    return redirect(request.referrer)



# =========================
# edit topio 
# =========================

@courses_bp.route('/topic/<int:topic_id>/edit', methods=['POST'])
@super_admin_required
def edit_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)

    new_code = request.form.get('topic_code', '').strip()
    new_title = request.form.get('topic_title', '').strip()
    new_co_id = request.form.get('co_id', type=int)

    if not new_code or not new_title or not new_co_id:
        flash('All fields are required', 'error')
        return redirect(request.referrer)

    # Validate CO belongs to same course
    co = CourseOutcome.query.filter_by(
        id=new_co_id,
        course_id=topic.course_id
    ).first()

    if not co:
        flash('Invalid CO selected', 'error')
        return redirect(request.referrer)

    # Prevent duplicate topic code in same course
    existing = Topic.query.filter(
        Topic.course_id == topic.course_id,
        Topic.code == new_code,
        Topic.id != topic.id
    ).first()

    if existing:
        flash('Another topic with this ID already exists', 'error')
        return redirect(request.referrer)

    topic.code = new_code
    topic.title = new_title
    topic.co_id = new_co_id

    db.session.commit()

    flash('Topic updated successfully', 'success')
    return redirect(request.referrer)


